"""
Enhanced headless authentication system with caching and security features.
"""
import graphene
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.utils import timezone
from graphql_jwt.shortcuts import get_token
from graphql_jwt.refresh_token.shortcuts import create_refresh_token
from core.infrastructure.cache.managers import user_cache
from api.models import UserProfile
import logging

logger = logging.getLogger(__name__)


class EnhancedTokenAuth(graphene.Mutation):
    """
    Enhanced JWT authentication with caching and additional security features.
    This is the proper headless authentication approach.
    """
    token = graphene.String()
    refresh_token = graphene.String()
    user = graphene.Field('api.schema.UserType')
    expires_in = graphene.Int()
    
    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)
        remember_me = graphene.Boolean(default_value=False)
    
    @classmethod
    def mutate(cls, root, info, username, password, remember_me=False):
        try:
            # Rate limiting check (can be implemented with Redis)
            client_ip = info.context.META.get('REMOTE_ADDR', 'unknown')
            if cls._is_rate_limited(client_ip, username):
                raise Exception('Too many login attempts. Please try again later.')
            
            # Authenticate user
            user = authenticate(username=username, password=password)
            
            if not user:
                cls._log_failed_attempt(client_ip, username)
                raise Exception('Invalid credentials provided')
            
            if not user.is_active:
                raise Exception('Account is disabled. Please contact support.')
            
            # Check if user profile exists
            try:
                profile = user.profile
            except UserProfile.DoesNotExist:
                raise Exception('User profile not found. Please contact support.')
            
            # Update last login
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            # Generate JWT token
            token = get_token(user)
            
            # Generate refresh token
            refresh_token = None
            try:
                refresh_token = create_refresh_token(user)
            except Exception as e:
                logger.warning(f"Could not create refresh token: {e}")
            
            # Cache user data for faster subsequent requests
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_active': user.is_active,
                'date_joined': user.date_joined.isoformat(),
                'last_login': user.last_login.isoformat(),
                'role': profile.role,
                'is_verified': profile.is_verified,
            }
            user_cache.cache_user(user_data)
            
            # Cache user permissions for faster authorization
            permissions = cls._get_user_permissions(user, profile)
            user_cache.cache_user_permissions(user.id, permissions)
            
            # Clear failed attempts on successful login
            cls._clear_failed_attempts(client_ip, username)
            
            # Token expiration time (for frontend)
            from django.conf import settings
            expires_in = getattr(settings, 'JWT_EXPIRATION_DELTA', 7200)
            if hasattr(expires_in, 'total_seconds'):
                expires_in = int(expires_in.total_seconds())
            
            logger.info(f"Successful login for user: {username} from IP: {client_ip}")
            
            return cls(
                token=token,
                refresh_token=refresh_token,
                user=user,
                expires_in=expires_in
            )
            
        except Exception as e:
            logger.error(f"Authentication error for {username}: {e}")
            raise e
    
    @staticmethod
    def _is_rate_limited(client_ip, username):
        """Check if client is rate limited (implement with Redis)."""
        from django.core.cache import cache
        
        # Check IP-based rate limiting
        ip_key = f"login_attempts:ip:{client_ip}"
        ip_attempts = cache.get(ip_key, 0)
        
        # Check username-based rate limiting
        username_key = f"login_attempts:username:{username}"
        username_attempts = cache.get(username_key, 0)
        
        # Rate limits: 10 attempts per IP per 15 minutes, 5 per username per 15 minutes
        return ip_attempts >= 10 or username_attempts >= 5
    
    @staticmethod
    def _log_failed_attempt(client_ip, username):
        """Log failed login attempt."""
        from django.core.cache import cache
        
        # Increment IP counter
        ip_key = f"login_attempts:ip:{client_ip}"
        ip_attempts = cache.get(ip_key, 0) + 1
        cache.set(ip_key, ip_attempts, 900)  # 15 minutes
        
        # Increment username counter
        username_key = f"login_attempts:username:{username}"
        username_attempts = cache.get(username_key, 0) + 1
        cache.set(username_key, username_attempts, 900)  # 15 minutes
        
        logger.warning(f"Failed login attempt for {username} from {client_ip}")
    
    @staticmethod
    def _clear_failed_attempts(client_ip, username):
        """Clear failed login attempts on successful login."""
        from django.core.cache import cache
        
        ip_key = f"login_attempts:ip:{client_ip}"
        username_key = f"login_attempts:username:{username}"
        
        cache.delete(ip_key)
        cache.delete(username_key)
    
    @staticmethod
    def _get_user_permissions(user, profile):
        """Get user permissions for caching."""
        permissions = {
            'role': profile.role,
            'can_create_articles': profile.role in ['writer', 'manager', 'admin'],
            'can_review_articles': profile.role in ['manager', 'admin'],
            'can_manage_users': profile.role in ['admin'],
            'can_manage_categories': profile.role in ['manager', 'admin'],
            'can_manage_tags': profile.role in ['manager', 'admin'],
            'can_view_dashboard': profile.role in ['writer', 'manager', 'admin'],
            'can_moderate_comments': profile.role in ['manager', 'admin'],
        }
        return permissions


class UserRegistration(graphene.Mutation):
    """
    User registration mutation - headless approach.
    """
    success = graphene.Boolean()
    message = graphene.String()
    user = graphene.Field('api.schema.UserType')
    token = graphene.String()
    
    class Arguments:
        username = graphene.String(required=True)
        email = graphene.String(required=True)
        password = graphene.String(required=True)
        first_name = graphene.String(required=True)
        last_name = graphene.String(required=True)
    
    @classmethod
    def mutate(cls, root, info, username, email, password, first_name, last_name):
        try:
            # Validate input
            if len(password) < 8:
                raise Exception('Password must be at least 8 characters long')
            
            if User.objects.filter(username=username).exists():
                raise Exception('Username already exists')
            
            if User.objects.filter(email=email).exists():
                raise Exception('Email already registered')
            
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Create user profile
            profile = UserProfile.objects.create(
                user=user,
                role='reader',  # Default role
                is_verified=False
            )
            
            # Generate token for immediate login
            token = get_token(user)
            
            # Cache user data
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_active': user.is_active,
                'date_joined': user.date_joined.isoformat(),
                'role': profile.role,
                'is_verified': profile.is_verified,
            }
            user_cache.cache_user(user_data)
            
            logger.info(f"New user registered: {username}")
            
            return cls(
                success=True,
                message="Registration successful",
                user=user,
                token=token
            )
            
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return cls(
                success=False,
                message=str(e),
                user=None,
                token=None
            )


class LogoutMutation(graphene.Mutation):
    """
    Logout mutation - clears cached user data.
    """
    success = graphene.Boolean()
    message = graphene.String()
    
    @classmethod
    def mutate(cls, root, info):
        user = info.context.user
        
        if user.is_authenticated:
            # Clear cached user data
            user_cache.invalidate_user(user.id, user.username)
            
            # In a real implementation, you might want to blacklist the JWT token
            # This requires additional infrastructure like Redis blacklist
            
            logger.info(f"User logged out: {user.username}")
            
            return cls(
                success=True,
                message="Logged out successfully"
            )
        
        return cls(
            success=False,
            message="User not authenticated"
        )


class ChangePassword(graphene.Mutation):
    """
    Change password mutation - headless approach.
    """
    success = graphene.Boolean()
    message = graphene.String()
    
    class Arguments:
        current_password = graphene.String(required=True)
        new_password = graphene.String(required=True)
    
    @classmethod
    def mutate(cls, root, info, current_password, new_password):
        user = info.context.user
        
        if not user.is_authenticated:
            raise Exception('Authentication required')
        
        try:
            # Verify current password
            if not user.check_password(current_password):
                raise Exception('Current password is incorrect')
            
            # Validate new password
            if len(new_password) < 8:
                raise Exception('New password must be at least 8 characters long')
            
            # Update password
            user.set_password(new_password)
            user.save()
            
            # Clear cached user data to force refresh
            user_cache.invalidate_user(user.id, user.username)
            
            logger.info(f"Password changed for user: {user.username}")
            
            return cls(
                success=True,
                message="Password changed successfully"
            )
            
        except Exception as e:
            logger.error(f"Password change error for {user.username}: {e}")
            return cls(
                success=False,
                message=str(e)
            )


# Enhanced authentication middleware
class CachedAuthenticationMiddleware:
    """
    Middleware to use cached user data for better performance.
    """
    
    def resolve(self, next, root, info, **args):
        # Check if user data is in cache
        user = info.context.user
        
        if user.is_authenticated and hasattr(user, 'id'):
            cached_user = user_cache.get_user_by_id(user.id)
            if cached_user:
                # Add cached data to context for faster access
                info.context.cached_user_data = cached_user
                
                # Check cached permissions
                cached_permissions = user_cache.get_user_permissions(user.id)
                if cached_permissions:
                    info.context.user_permissions = cached_permissions
        
        return next(root, info, **args)


# Usage in your schema.py:
"""
# In your newsor/schema.py, replace the existing authentication with:

class Mutation(ApiMutation, graphene.ObjectType):
    # Enhanced authentication mutations
    token_auth = EnhancedTokenAuth.Field()
    register = UserRegistration.Field()
    logout = LogoutMutation.Field()
    change_password = ChangePassword.Field()
    
    # Standard JWT mutations (keep these for compatibility)
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()
"""
