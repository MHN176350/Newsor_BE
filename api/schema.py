import graphene
from graphene_django import DjangoObjectType
from django.contrib.auth.models import User
from .models import (
    Category, Tag, UserProfile, News, Comment, 
    Like, ReadingHistory, NewsletterSubscription, ArticleImage
)
from .utils import sanitize_html_content, get_cloudinary_upload_signature
import base64
import io
from PIL import Image
import cloudinary.uploader
import uuid
from .cloudinary_utils import CloudinaryUtils


class UserType(DjangoObjectType):
    """
    GraphQL User type
    """
    profile = graphene.Field(lambda: UserProfileType)
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'date_joined', 'last_login')

    def resolve_profile(self, info):
        """
        Resolve user profile
        """
        try:
            return self.profile
        except UserProfile.DoesNotExist:
            return None


class CategoryType(DjangoObjectType):
    """
    GraphQL Category type
    """
    article_count = graphene.Int()
    
    class Meta:
        model = Category
        fields = '__all__'
    
    def resolve_article_count(self, info):
        """
        Resolve the number of published articles in this category
        """
        return self.news_set.filter(status='published').count()


class TagType(DjangoObjectType):
    """
    GraphQL Tag type
    """
    class Meta:
        model = Tag
        fields = '__all__'


class UserProfileType(DjangoObjectType):
    """
    GraphQL UserProfile type
    """
    avatar_url = graphene.String()  # Custom field for avatar URL
    has_write_permission = graphene.Boolean()
    has_admin_permission = graphene.Boolean()
    has_manager_permission = graphene.Boolean()
    
    class Meta:
        model = UserProfile
        exclude = ['avatar']  # Exclude the CloudinaryField from auto-generation
    
    def resolve_avatar_url(self, info):
        """
        Resolve avatar URL with fallback to default image
        """
        avatar_url = self.avatar_url  # Use the new property method
        if avatar_url:
            return avatar_url
        else:
            # Return default avatar if no avatar is set
            return "/static/images/default-avatar.svg"
    
    def resolve_has_write_permission(self, info):
        """Check if user has write permission"""
        return self.role.lower() in ['writer', 'manager', 'admin']
    
    def resolve_has_admin_permission(self, info):
        """Check if user has admin permission"""
        return self.role.lower() == 'admin'
    
    def resolve_has_manager_permission(self, info):
        """Check if user has manager permission"""
        return self.role.lower() in ['manager', 'admin']


class NewsType(DjangoObjectType):
    """
    GraphQL News type
    """
    featured_image_url = graphene.String()  # Custom field for featured image URL
    likes_count = graphene.Int()
    comments_count = graphene.Int()
    read_count = graphene.Int()
    is_liked_by_user = graphene.Boolean()
    
    class Meta:
        model = News
        exclude = ['featured_image']  # Exclude the CloudinaryField from auto-generation
    
    def resolve_featured_image_url(self, info):
        """
        Resolve featured image URL with fallback to default image
        """
        featured_image_url = self.featured_image_url  # Use the new property method
        if featured_image_url:
            return featured_image_url
        else:
            # Return default news image if no image is set
            return "/static/images/default-news.svg"
    
    def resolve_likes_count(self, info):
        """
        Get the number of likes for this article
        """
        return self.likes.count()
    
    def resolve_comments_count(self, info):
        """
        Get the number of comments for this article
        """
        return self.comments.count()
    
    def resolve_read_count(self, info):
        """
        Get the read count (view count) for this article
        """
        return self.view_count
    
    def resolve_is_liked_by_user(self, info):
        """
        Check if the current user has liked this article
        """
        user = info.context.user
        if not user.is_authenticated:
            return False
        return self.likes.filter(user=user).exists()


class CommentType(DjangoObjectType):
    """
    GraphQL Comment type
    """
    class Meta:
        model = Comment
        fields = '__all__'


class ArticleImageType(DjangoObjectType):
    """
    GraphQL ArticleImage type
    """
    image_url = graphene.String()
    
    class Meta:
        model = ArticleImage
        exclude = ['image']  # Exclude the CloudinaryField from auto-generation
    
    def resolve_image_url(self, info):
        """
        Resolve image URL
        """
        image_url = self.image_url  # Use the new property method
        return image_url or ""
        return ""


class LikeType(DjangoObjectType):
    """
    GraphQL Like type
    """
    class Meta:
        model = Like
        fields = '__all__'


class ReadingHistoryType(DjangoObjectType):
    """
    GraphQL ReadingHistory type
    """
    class Meta:
        model = ReadingHistory
        fields = '__all__'


class NewsletterSubscriptionType(DjangoObjectType):
    """
    GraphQL NewsletterSubscription type
    """
    class Meta:
        model = NewsletterSubscription
        fields = '__all__'


class DashboardStatsType(graphene.ObjectType):
    """
    Dashboard statistics type
    """
    # User statistics
    total_users = graphene.Int()
    total_readers = graphene.Int()
    total_writers = graphene.Int()
    total_managers = graphene.Int()
    total_admins = graphene.Int()
    new_users_this_month = graphene.Int()
    
    # News statistics
    total_news = graphene.Int()
    published_news = graphene.Int()
    draft_news = graphene.Int()
    pending_news = graphene.Int()
    rejected_news = graphene.Int()
    news_this_month = graphene.Int()
    
    # Category and Tag statistics
    total_categories = graphene.Int()
    total_tags = graphene.Int()
    
    # Activity statistics
    total_views = graphene.Int()
    total_likes = graphene.Int()
    total_comments = graphene.Int()


class RecentActivityType(graphene.ObjectType):
    """
    Recent activity type
    """
    id = graphene.ID()
    action = graphene.String()
    description = graphene.String()
    timestamp = graphene.DateTime()
    user = graphene.Field(UserType)


class Query(graphene.ObjectType):
    """
    API GraphQL Queries
    """
    # Basic queries
    hello = graphene.String(name=graphene.String(default_value='World'))
    
    # User queries
    me = graphene.Field(UserType)
    users = graphene.List(UserType)
    user = graphene.Field(UserType, id=graphene.Int(required=True))
    user_profile = graphene.Field(UserProfileType, user_id=graphene.Int(required=True))
    
    # News queries
    news_list = graphene.List(NewsType, 
                             status=graphene.String(),
                             category_id=graphene.Int(),
                             author_id=graphene.Int(),
                             search=graphene.String(),
                             tag_id=graphene.Int())
    news_article = graphene.Field(NewsType, id=graphene.Int(), slug=graphene.String())
    published_news = graphene.List(NewsType,
                                  search=graphene.String(),
                                  category_id=graphene.Int(),
                                  tag_id=graphene.Int())
    news_for_review = graphene.List(NewsType)
    my_news = graphene.List(NewsType)
    
    # Category and Tag queries
    categories = graphene.List(CategoryType)
    category = graphene.Field(CategoryType, id=graphene.Int())
    tags = graphene.List(TagType)
    
    # Comment queries
    article_comments = graphene.List(CommentType, article_id=graphene.Int(required=True))
    
    # Analytics queries
    user_reading_history = graphene.List(ReadingHistoryType, user_id=graphene.Int(required=True))
    
    # Dashboard queries
    dashboard_stats = graphene.Field(DashboardStatsType)
    recent_activity = graphene.List(RecentActivityType, limit=graphene.Int())

    def resolve_hello(self, info, name):
       
        return f'Hello {name}'
    
    def resolve_me(self, info):
        """Get current authenticated user"""
        user = info.context.user
        if user.is_authenticated:
            return user
        return None

    def resolve_users(self, info):
        """Get all users"""
        return User.objects.all()

    def resolve_user(self, info, id):
        """Get user by ID"""
        try:
            return User.objects.get(pk=id)
        except User.DoesNotExist:
            return None

    def resolve_user_profile(self, info, user_id):
        """Get user profile by user ID"""
        try:
            return UserProfile.objects.get(user_id=user_id)
        except UserProfile.DoesNotExist:
            return None

    def resolve_news_list(self, info, status=None, category_id=None, author_id=None, search=None, tag_id=None):
        """Get news articles with optional filters"""
        from django.db.models import Q
        
        queryset = News.objects.all()
        
        if status:
            queryset = queryset.filter(status=status)
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if author_id:
            queryset = queryset.filter(author_id=author_id)
        if tag_id:
            queryset = queryset.filter(tags__id=tag_id)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(content__icontains=search) |
                Q(excerpt__icontains=search) |
                Q(meta_keywords__icontains=search)
            )
            
        return queryset.distinct().order_by('-created_at')

    def resolve_news_article(self, info, id=None, slug=None):
        """Get news article by ID or slug"""
        try:
            if id:
                return News.objects.get(pk=id)
            elif slug:
                return News.objects.get(slug=slug)
        except News.DoesNotExist:
            return None

    def resolve_published_news(self, info, search=None, category_id=None, tag_id=None):
        """Get published news articles with optional filters"""
        from django.db.models import Q
        
        queryset = News.objects.filter(status='published')
        
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if tag_id:
            queryset = queryset.filter(tags__id=tag_id)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(content__icontains=search) |
                Q(excerpt__icontains=search) |
                Q(meta_keywords__icontains=search)
            )
            
        return queryset.distinct().order_by('-published_at')

    def resolve_categories(self, info):
        """Get all categories"""
        return Category.objects.filter(is_active=True)

    def resolve_category(self, info, id):
        """Get category by ID"""
        try:
            return Category.objects.get(pk=id)
        except Category.DoesNotExist:
            return None

    def resolve_tags(self, info):
        """Get all tags"""
        return Tag.objects.all()

    def resolve_news_for_review(self, info):
        """Get news articles that need review (for managers)"""
        # Only allow managers and admins to access this
        user = info.context.user
        if not user.is_authenticated:
            return []
        
        try:
            profile = UserProfile.objects.get(user=user)
            if profile.role.lower() not in ['manager', 'admin']:
                return []
        except UserProfile.DoesNotExist:
            return []
        
        # Return articles that are in draft or pending status
        return News.objects.filter(status__in=['draft', 'pending']).order_by('-created_at')

    def resolve_my_news(self, info):
        """Get current user's news articles"""
        user = info.context.user
        if not user.is_authenticated:
            return []
        
        # Return all articles by the current user
        return News.objects.filter(author=user).order_by('-created_at')

    def resolve_article_comments(self, info, article_id):
        """Get comments for an article"""
        return Comment.objects.filter(article_id=article_id, status='approved')

    def resolve_user_reading_history(self, info, user_id):
        """Get user's reading history"""
        return ReadingHistory.objects.filter(user_id=user_id)
    
    def resolve_dashboard_stats(self, info):
        """Get dashboard statistics"""
        from datetime import datetime
        from django.db.models import Count, Sum
        
        # Check if user is admin or manager
        user = info.context.user
        if not user.is_authenticated:
            return None
            
        try:
            profile = UserProfile.objects.get(user=user)
            if profile.role.lower() not in ['admin', 'manager']:
                return None
        except UserProfile.DoesNotExist:
            return None
        
        # Calculate statistics
        current_month = datetime.now().replace(day=1)
        
        # User statistics
        total_users = User.objects.count()
        user_roles = UserProfile.objects.values('role').annotate(count=Count('role'))
        role_counts = {role['role']: role['count'] for role in user_roles}
        
        new_users_this_month = User.objects.filter(date_joined__gte=current_month).count()
        
        # News statistics
        news_stats = News.objects.values('status').annotate(count=Count('status'))
        status_counts = {stat['status']: stat['count'] for stat in news_stats}
        
        news_this_month = News.objects.filter(created_at__gte=current_month).count()
        
        # Category and Tag statistics
        total_categories = Category.objects.filter(is_active=True).count()
        total_tags = Tag.objects.count()
        
        # Activity statistics (using model fields)
        total_views = News.objects.aggregate(total=Sum('view_count'))['total'] or 0
        total_likes = News.objects.aggregate(total=Sum('like_count'))['total'] or 0
        total_comments = Comment.objects.count() if hasattr(Comment, 'objects') else 0
        
        return DashboardStatsType(
            # User statistics
            total_users=total_users,
            total_readers=role_counts.get('reader', 0),
            total_writers=role_counts.get('writer', 0),
            total_managers=role_counts.get('manager', 0),
            total_admins=role_counts.get('admin', 0),
            new_users_this_month=new_users_this_month,
            
            # News statistics
            total_news=News.objects.count(),
            published_news=status_counts.get('published', 0),
            draft_news=status_counts.get('draft', 0),
            pending_news=status_counts.get('pending', 0),
            rejected_news=status_counts.get('rejected', 0),
            news_this_month=news_this_month,
            
            # Category and Tag statistics
            total_categories=total_categories,
            total_tags=total_tags,
            
            # Activity statistics
            total_views=total_views,
            total_likes=total_likes,
            total_comments=total_comments,
        )
    
    def resolve_recent_activity(self, info, limit=10):
        """Get recent activity"""
        user = info.context.user
        if not user.is_authenticated:
            return []
            
        try:
            profile = UserProfile.objects.get(user=user)
            if profile.role.lower() not in ['admin', 'manager']:
                return []
        except UserProfile.DoesNotExist:
            return []
        
        # Get recent news as activity
        recent_news = News.objects.select_related('author').order_by('-created_at')[:limit]
        
        activities = []
        for news in recent_news:
            activities.append(RecentActivityType(
                id=news.id,
                action='news_created',
                description=f'New article "{news.title}" was created',
                timestamp=news.created_at,
                user=news.author
            ))
        
        return activities

    # ...existing code...
    
class CreateUser(graphene.Mutation):
    """
    Create a new user with profile
    """
    class Arguments:
        username = graphene.String(required=True)
        email = graphene.String(required=True)
        password = graphene.String(required=True)
        first_name = graphene.String()
        last_name = graphene.String()
        avatar = graphene.String()  # Cloudinary URL or base64 image data

    user = graphene.Field(UserType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, username, email, password, first_name=None, last_name=None, avatar=None):
        """
        Create user mutation with profile creation
        """
        try:
            # Check if user already exists
            if User.objects.filter(username=username).exists():
                return CreateUser(success=False, errors=['Username already exists'])
            
            if User.objects.filter(email=email).exists():
                return CreateUser(success=False, errors=['Email already exists'])

            # Create new user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name or '',
                last_name=last_name or ''
            )
            
            # Create user profile
            profile = UserProfile.objects.create(
                user=user,
                role='reader',
                is_verified=False
            )
            
            # Handle avatar if provided
            if avatar:
                try:
                    # If avatar is a Cloudinary URL, save it directly
                    if avatar.startswith('http'):
                        profile.avatar = avatar
                        profile.save()
                except Exception:
                    # If avatar processing fails, continue without avatar
                    pass
            
            return CreateUser(user=user, success=True, errors=[])
        
        except Exception as e:
            return CreateUser(success=False, errors=[str(e)])


class UpdateUserProfile(graphene.Mutation):
    """
    Update user profile
    """
    class Arguments:
        bio = graphene.String()
        phone = graphene.String()
        date_of_birth = graphene.Date()
        avatar = graphene.String()  # Cloudinary URL

    profile = graphene.Field(UserProfileType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, bio=None, phone=None, date_of_birth=None, avatar=None):
        """
        Update user profile mutation
        """
        user = info.context.user
        if not user.is_authenticated:
            return UpdateUserProfile(success=False, errors=['Authentication required'])

        try:
            profile = UserProfile.objects.get(user=user)
            
            if bio is not None:
                profile.bio = bio
            if phone is not None:
                profile.phone = phone
            if date_of_birth is not None:
                profile.date_of_birth = date_of_birth
            if avatar is not None:
                profile.avatar = avatar
                
            profile.save()
            
            return UpdateUserProfile(profile=profile, success=True, errors=[])
        
        except UserProfile.DoesNotExist:
            return UpdateUserProfile(success=False, errors=['Profile not found'])
        except Exception as e:
            return UpdateUserProfile(success=False, errors=[str(e)])


class CreateNews(graphene.Mutation):
    """
    Create a new news article (for writers)
    """
    class Arguments:
        title = graphene.String(required=True)
        content = graphene.String(required=True)
        excerpt = graphene.String(required=True)
        category_id = graphene.Int(required=True)
        tag_ids = graphene.List(graphene.Int)
        featured_image = graphene.String()  # Cloudinary URL
        meta_description = graphene.String()
        meta_keywords = graphene.String()

    news = graphene.Field(NewsType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, title, content, excerpt, category_id, tag_ids=None, 
               featured_image=None, meta_description=None, meta_keywords=None):
        """
        Create news article mutation
        """
        user = info.context.user
        if not user.is_authenticated:
            return CreateNews(success=False, errors=['Authentication required'])

        try:
            # Check if user has writer role or higher
            profile = UserProfile.objects.get(user=user)
            if profile.role.lower() not in ['writer', 'manager', 'admin']:
                return CreateNews(success=False, errors=['Permission denied. Writer role required.'])

            # Check if category exists
            try:
                category = Category.objects.get(id=category_id)
            except Category.DoesNotExist:
                return CreateNews(success=False, errors=['Category not found'])

            # Create slug from title
            from django.utils.text import slugify
            slug = slugify(title)
            
            # Ensure slug is unique
            counter = 1
            original_slug = slug
            while News.objects.filter(slug=slug).exists():
                slug = f"{original_slug}-{counter}"
                counter += 1

            # Sanitize HTML content
            sanitized_content = sanitize_html_content(content)

            # Create news article
            news = News.objects.create(
                title=title,
                slug=slug,
                content=sanitized_content,
                excerpt=excerpt,
                author=user,
                category=category,
                featured_image=featured_image or '',
                meta_description=meta_description or '',
                meta_keywords=meta_keywords or '',
                status='draft'  # Default to draft
            )

            # Add tags if provided
            if tag_ids:
                tags = Tag.objects.filter(id__in=tag_ids)
                news.tags.set(tags)

            return CreateNews(news=news, success=True, errors=[])

        except UserProfile.DoesNotExist:
            return CreateNews(success=False, errors=['User profile not found'])
        except Exception as e:
            return CreateNews(success=False, errors=[str(e)])
        
class CreateCategory(graphene.Mutation):
    """
    Create a new category
    """

    class Arguments:
        name = graphene.String(required=True)
        slug = graphene.String(required=True)
        description = graphene.String(required=True)
    category = graphene.Field(CategoryType)
    success = graphene.Boolean()
    errors = graphene.String()

    def mutate(self, info, name, slug, description=""):
        try:
            # Check name and slug existed
            if Category.objects.filter(slug=slug).exists():
                return CreateCategory(success=False, errors="Slug already exists.", category=None)
            if Category.objects.filter(name=name).exists():
                return CreateCategory(success=False, errors="Name already exists.", category=None)

            # Create new Category
            
            category = Category.objects.create(
                name=name,
                slug=slug,
                description=description,
            )
            return CreateCategory(category = category, success=True, errors="Category created successfully.")
        except Exception as e:
            return CreateCategory(success=False, errors="Unexpected error: " + str(e), category=None)
        
class CreateTag(graphene.Mutation):
    """
    Create a new tag
    """

    class Arguments:
        name = graphene.String(required=True)
        slug = graphene.String(required=True)
    tag = graphene.Field(TagType)
    success = graphene.Boolean()
    errors = graphene.String()

    def mutate(self, info, name, slug, description=""):
        try:
            # Check name and slug existed
            if Tag.objects.filter(slug=slug).exists():
                return CreateTag(success=False, errors="Slug already exists.", tag=None)
            if Tag.objects.filter(name=name).exists():
                return CreateTag(success=False, errors="Name already exists.", tag=None)

            # Create new Tag
            
            tag = Tag.objects.create(
                name=name,
                slug=slug,
            )
            return CreateTag(tag = tag, success=True, errors="Tag created successfully.")
        except Exception as e:
            return CreateTag(success=False, errors="Unexpected error: " + str(e), tag=None)
        
class CreateComment(graphene.Mutation):
    """
    Create a new comment
    """

    class Arguments:
        article_id = graphene.ID(required=True)
        content = graphene.String(required=True)
        parent_id = graphene.ID(required=False)

    comment = graphene.Field(CommentType)
    success = graphene.Boolean()
    errors = graphene.String()

    def mutate(self, info, article_id, content, parent_id=None):
        try:
            user = info.context.user

            # Check user authentication
            if user.is_anonymous:
                return CreateComment(success=False, errors="Authentication required.", comment=None)

            # Check if the article exists
            try:
                article = News.objects.get(pk=article_id)
            except News.DoesNotExist:
                return CreateComment(success=False, errors="Article not found.", comment=None)

            # Check if parent comment exists, if provided
            parent = None
            if parent_id:
                try:
                    parent = Comment.objects.get(pk=parent_id, article=article)
                except Comment.DoesNotExist:
                    return CreateComment(success=False, errors="Parent comment not found.", comment=None)

            # Create new comment
            comment = Comment.objects.create(
                article=article,
                author=user,
                content=content,
                parent=parent,
            )

            return CreateComment(comment=comment, success=True, errors="Comment created successfully.")

        except Exception as e:
            return CreateComment(success=False, errors="Unexpected error: " + str(e), comment=None)

class ChangeUserRole(graphene.Mutation):
    """
    Change user role (admin only)
    """
    class Arguments:
        user_id = graphene.Int(required=True)
        new_role = graphene.String(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    user = graphene.Field(UserType)

    def mutate(self, info, user_id, new_role):
        """
        Change user role mutation (admin only)
        """
        current_user = info.context.user
        if not current_user.is_authenticated:
            return ChangeUserRole(success=False, errors=['Authentication required'])

        try:
            # Check if current user is admin
            current_profile = UserProfile.objects.get(user=current_user)
            if current_profile.role.lower() != 'admin':
                return ChangeUserRole(success=False, errors=['Admin privileges required'])

            # Validate new role
            valid_roles = ['reader', 'writer', 'manager', 'admin']
            if new_role not in valid_roles:
                return ChangeUserRole(success=False, errors=[f'Invalid role. Must be one of: {", ".join(valid_roles)}'])

            # Get target user
            target_user = User.objects.get(id=user_id)
            target_profile, created = UserProfile.objects.get_or_create(
                user=target_user,
                defaults={'role': new_role}
            )
            
            if not created:
                target_profile.role = new_role
                target_profile.save()

            return ChangeUserRole(success=True, errors=[], user=target_user)

        except UserProfile.DoesNotExist:
            return ChangeUserRole(success=False, errors=['User profile not found'])
        except User.DoesNotExist:
            return ChangeUserRole(success=False, errors=['User not found'])
        except Exception as e:
            return ChangeUserRole(success=False, errors=[str(e)])


class GetCloudinarySignature(graphene.Mutation):
    """
    Get signed upload parameters for Cloudinary
    """
    signature = graphene.String()
    timestamp = graphene.String()
    api_key = graphene.String()
    cloud_name = graphene.String()
    folder = graphene.String()
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info):
        """
        Generate Cloudinary upload signature
        """
        user = info.context.user
        if not user.is_authenticated:
            return GetCloudinarySignature(success=False, errors=['Authentication required'])

        try:
            # Check if user has writer role or higher
            profile = UserProfile.objects.get(user=user)
            if profile.role.lower() not in ['writer', 'manager', 'admin']:
                return GetCloudinarySignature(success=False, errors=['Permission denied. Writer role required.'])

            upload_params = get_cloudinary_upload_signature()
            
            return GetCloudinarySignature(
                signature=upload_params['signature'],
                timestamp=str(upload_params['timestamp']),
                api_key=upload_params['api_key'],
                cloud_name=upload_params['cloud_name'],
                folder=upload_params['folder'],
                success=True,
                errors=[]
            )

        except UserProfile.DoesNotExist:
            return GetCloudinarySignature(success=False, errors=['User profile not found'])
        except Exception as e:
            return GetCloudinarySignature(success=False, errors=[str(e)])


class UploadBase64Image(graphene.Mutation):
    """
    Upload base64 image to Cloudinary with proper sizing and optimization
    """
    class Arguments:
        base64_data = graphene.String(required=True, description="Base64 encoded image data")
        folder = graphene.String(default_value="newsor/uploads", description="Cloudinary folder")
        max_width = graphene.Int(default_value=800, description="Maximum width for resizing")
        max_height = graphene.Int(default_value=600, description="Maximum height for resizing")
        quality = graphene.String(default_value="auto", description="Image quality (auto, 100, 80, etc.)")
        format = graphene.String(default_value="auto", description="Image format (auto, jpg, png, webp)")

    url = graphene.String()
    public_id = graphene.String()
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, base64_data, folder="newsor/uploads", max_width=800, max_height=600, quality="auto", format="auto"):
        """
        Process base64 image and upload to Cloudinary
        """
        try:
            # Remove data URL prefix if present
            if base64_data.startswith('data:image'):
                base64_data = base64_data.split(',')[1]
            
            # Decode base64 data
            try:
                image_data = base64.b64decode(base64_data)
            except Exception as e:
                return UploadBase64Image(success=False, errors=[f"Invalid base64 data: {str(e)}"])
            
            # Open image with PIL
            try:
                image = Image.open(io.BytesIO(image_data))
            except Exception as e:
                return UploadBase64Image(success=False, errors=[f"Invalid image data: {str(e)}"])
            
            # Convert RGBA to RGB if necessary
            if image.mode == 'RGBA':
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1])
                image = background
            
            # Only resize if image is significantly larger than target
            # Use a more gentle approach to preserve quality
            if image.width > max_width * 1.5 or image.height > max_height * 1.5:
                # Calculate new size maintaining aspect ratio
                ratio = min(max_width / image.width, max_height / image.height)
                new_width = int(image.width * ratio)
                new_height = int(image.height * ratio)
                
                # Use high-quality resampling
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            # If image is only slightly larger, keep original size
            
            # Convert back to bytes (use high quality to preserve image fidelity)
            output = io.BytesIO()
            if image.mode == 'RGBA':
                # For PNG with transparency, save as PNG
                image.save(output, format='PNG', optimize=False)
            else:
                # For regular images, save as JPEG with maximum quality
                image.save(output, format='JPEG', quality=95, optimize=False)
            output.seek(0)
            
            # Generate unique filename
            unique_filename = f"upload_{uuid.uuid4().hex}"
            
            # Upload to Cloudinary with minimal processing to preserve quality
            upload_result = cloudinary.uploader.upload(
                output.getvalue(),
                public_id=unique_filename,
                folder=folder,
                # Remove quality transformation to avoid double compression
                # Let Cloudinary handle optimization automatically
                resource_type="image",
                quality="auto:best"  # Use Cloudinary's best automatic quality
            )
            
            # Optimize URL for storage
            optimized_url = CloudinaryUtils.optimize_for_storage(upload_result['secure_url'])
            
            return UploadBase64Image(
                url=optimized_url,
                public_id=upload_result['public_id'],
                success=True,
                errors=[]
            )
            
        except Exception as e:
            return UploadBase64Image(success=False, errors=[f"Upload failed: {str(e)}"])


class UploadAvatarImage(graphene.Mutation):
    """
    Upload and set avatar image for user profile
    """
    class Arguments:
        base64_data = graphene.String(required=True, description="Base64 encoded avatar image")

    profile = graphene.Field(UserProfileType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, base64_data):
        """
        Upload avatar and update user profile
        """
        user = info.context.user
        if not user.is_authenticated:
            return UploadAvatarImage(success=False, errors=['Authentication required'])

        try:
            # Upload the image with avatar-specific settings
            upload_mutation = UploadBase64Image()
            upload_result = upload_mutation.mutate(
                info, 
                base64_data=base64_data,
                folder="newsor/avatars",
                max_width=400,
                max_height=400,
                quality="auto",
                format="auto"
            )
            
            if not upload_result.success:
                return UploadAvatarImage(success=False, errors=upload_result.errors)
            
            # Update user profile with new avatar
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.avatar = upload_result.url
            profile.save()
            
            return UploadAvatarImage(profile=profile, success=True, errors=[])
            
        except Exception as e:
            return UploadAvatarImage(success=False, errors=[f"Avatar upload failed: {str(e)}"])


class UpdateNewsStatus(graphene.Mutation):
    """
    Update news article status (for managers)
    """
    class Arguments:
        id = graphene.Int(required=True)
        status = graphene.String(required=True)
        review_comment = graphene.String()

    news = graphene.Field(NewsType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id, status, review_comment=None):
        """
        Update news article status mutation
        """
        user = info.context.user
        if not user.is_authenticated:
            return UpdateNewsStatus(success=False, errors=['Authentication required'])

        try:
            # Check if user has manager role or higher
            profile = UserProfile.objects.get(user=user)
            if profile.role.lower() not in ['manager', 'admin']:
                return UpdateNewsStatus(success=False, errors=['Permission denied. Manager role required.'])

            # Get the news article
            try:
                news = News.objects.get(id=id)
            except News.DoesNotExist:
                return UpdateNewsStatus(success=False, errors=['News article not found'])

            # Validate status
            valid_statuses = ['draft', 'pending', 'published', 'rejected']
            if status not in valid_statuses:
                return UpdateNewsStatus(success=False, errors=['Invalid status'])

            # Update the news article
            news.status = status
            if status == 'published':
                from django.utils import timezone
                news.published_at = timezone.now()
            
            news.save()

            # TODO: Add review comment handling if needed (would require a separate model)
            # For now, we'll just update the status

            return UpdateNewsStatus(news=news, success=True, errors=[])

        except UserProfile.DoesNotExist:
            return UpdateNewsStatus(success=False, errors=['User profile not found'])
        except Exception as e:
            return UpdateNewsStatus(success=False, errors=[str(e)])


class UpdateNews(graphene.Mutation):
    """
    Update an existing news article (for writers)
    """
    class Arguments:
        id = graphene.Int(required=True)
        title = graphene.String(required=True)
        content = graphene.String(required=True)
        excerpt = graphene.String(required=True)
        category_id = graphene.Int(required=True)
        tag_ids = graphene.List(graphene.Int)
        featured_image = graphene.String()  # Cloudinary URL
        meta_description = graphene.String()
        meta_keywords = graphene.String()

    news = graphene.Field(NewsType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id, title, content, excerpt, category_id, tag_ids=None, 
               featured_image=None, meta_description=None, meta_keywords=None):
        """
        Update news article mutation
        """
        user = info.context.user
        if not user.is_authenticated:
            return UpdateNews(success=False, errors=['Authentication required'])

        try:
            # Check if user has writer role or higher
            profile = UserProfile.objects.get(user=user)
            if profile.role.lower() not in ['writer', 'manager', 'admin']:
                return UpdateNews(success=False, errors=['Permission denied. Writer role required.'])

            # Get the existing news article
            try:
                news = News.objects.get(id=id)
            except News.DoesNotExist:
                return UpdateNews(success=False, errors=['Article not found'])

            # Check if user owns the article (unless they're admin/manager)
            if profile.role.lower() not in ['admin', 'manager'] and news.author.id != user.id:
                return UpdateNews(success=False, errors=['Permission denied. You can only edit your own articles.'])

            # Check if article can be edited (only drafts and rejected articles)
            if news.status.lower() not in ['draft', 'rejected']:
                return UpdateNews(success=False, errors=['You can only edit articles that are in draft or rejected status.'])

            # Check if category exists
            try:
                category = Category.objects.get(id=category_id)
            except Category.DoesNotExist:
                return UpdateNews(success=False, errors=['Category not found'])

            # Sanitize HTML content
            sanitized_content = sanitize_html_content(content)

            # Update news article
            news.title = title
            news.content = sanitized_content
            news.excerpt = excerpt
            news.category = category
            news.featured_image = featured_image or ''
            news.meta_description = meta_description or ''
            news.meta_keywords = meta_keywords or ''
            
            # Update slug if title changed
            from django.utils.text import slugify
            new_slug = slugify(title)
            if new_slug != news.slug:
                # Ensure slug is unique
                counter = 1
                original_slug = new_slug
                while News.objects.filter(slug=new_slug).exclude(id=id).exists():
                    new_slug = f"{original_slug}-{counter}"
                    counter += 1
                news.slug = new_slug
            
            news.save()

            # Update tags if provided
            if tag_ids is not None:
                tags = Tag.objects.filter(id__in=tag_ids)
                news.tags.set(tags)

            return UpdateNews(news=news, success=True, errors=[])

        except UserProfile.DoesNotExist:
            return UpdateNews(success=False, errors=['User profile not found'])
        except Exception as e:
            return UpdateNews(success=False, errors=[str(e)])


class ToggleLike(graphene.Mutation):
    """
    Toggle like/unlike for articles or comments
    """
    class Arguments:
        news_id = graphene.Int()
        comment_id = graphene.Int()

    success = graphene.Boolean()
    liked = graphene.Boolean()
    likes_count = graphene.Int()
    errors = graphene.List(graphene.String)

    def mutate(self, info, news_id=None, comment_id=None):
        """
        Toggle like mutation
        """
        user = info.context.user
        if not user.is_authenticated:
            return ToggleLike(success=False, errors=['Authentication required'])

        try:
            # Validate input - must provide either news_id or comment_id
            if not news_id and not comment_id:
                return ToggleLike(success=False, errors=['Must provide either news_id or comment_id'])
            
            if news_id and comment_id:
                return ToggleLike(success=False, errors=['Cannot like both news and comment in same request'])

            if news_id:
                # Handle news like
                try:
                    news = News.objects.get(id=news_id)
                except News.DoesNotExist:
                    return ToggleLike(success=False, errors=['News article not found'])

                like, created = Like.objects.get_or_create(
                    user=user,
                    article=news,
                    defaults={'comment': None}
                )

                if not created:
                    # Unlike - remove the like
                    like.delete()
                    liked = False
                else:
                    # Like created
                    liked = True

                # Get updated like count
                likes_count = news.likes.count()
                
                return ToggleLike(
                    success=True,
                    liked=liked,
                    likes_count=likes_count,
                    errors=[]
                )

            elif comment_id:
                # Handle comment like
                try:
                    comment = Comment.objects.get(id=comment_id)
                except Comment.DoesNotExist:
                    return ToggleLike(success=False, errors=['Comment not found'])

                like, created = Like.objects.get_or_create(
                    user=user,
                    comment=comment,
                    defaults={'article': None}
                )

                if not created:
                    # Unlike - remove the like
                    like.delete()
                    liked = False
                else:
                    # Like created
                    liked = True

                # Get updated like count
                likes_count = comment.likes.count()
                
                return ToggleLike(
                    success=True,
                    liked=liked,
                    likes_count=likes_count,
                    errors=[]
                )

        except Exception as e:
            return ToggleLike(success=False, errors=[str(e)])

# ...existing mutations...

class Mutation(graphene.ObjectType):
    """
    API GraphQL Mutations
    """
    create_user = CreateUser.Field()
    update_user_profile = UpdateUserProfile.Field()
    create_news = CreateNews.Field()
    create_category = CreateCategory.Field()
    create_tag = CreateTag.Field()
    create_comment = CreateComment.Field()
    change_user_role = ChangeUserRole.Field()
    get_cloudinary_signature = GetCloudinarySignature.Field()
    upload_base64_image = UploadBase64Image.Field()
    upload_avatar_image = UploadAvatarImage.Field()
    update_news_status = UpdateNewsStatus.Field()
    update_news = UpdateNews.Field()
    toggle_like = ToggleLike.Field()
    toggle_like = ToggleLike.Field()

# Schema
schema = graphene.Schema(query=Query, mutation=Mutation)
