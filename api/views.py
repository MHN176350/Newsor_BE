from django.http import JsonResponse
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User
from .models import UserProfile
from .serializers import (
    UserRegistrationSerializer, 
    UserResponseSerializer,
    UserProfileSerializer
)


def health_check(request):
    """
    Simple health check endpoint
    """
    return JsonResponse({
        'status': 'healthy',
        'message': 'Newsor API is running successfully'
    })


class UserRegistrationView(APIView):
   
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """
        Register a new user
        
        Expected payload:
        {
            "username": "john_doe",
            "email": "john@example.com",
            "password": "securepassword123",
            "password_confirm": "securepassword123",
            "first_name": "John",
            "last_name": "Doe"
        }
        """
        serializer = UserRegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            
            # Return user data with profile
            response_serializer = UserResponseSerializer(user)
            
            return Response({
                'success': True,
                'message': 'User registered successfully',
                'user': response_serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'message': 'Registration failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_profile_view(request):
    """
    Get current user's profile information
    """
    try:
        profile = UserProfile.objects.get(user=request.user)
        serializer = UserProfileSerializer(profile)
        
        return Response({
            'success': True,
            'profile': serializer.data
        })
    except UserProfile.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Profile not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def update_profile_view(request):
    """
    Update current user's profile information
    """
    try:
        profile = UserProfile.objects.get(user=request.user)
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            
            return Response({
                'success': True,
                'message': 'Profile updated successfully',
                'profile': serializer.data
            })
        
        return Response({
            'success': False,
            'message': 'Update failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except UserProfile.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Profile not found'
        }, status=status.HTTP_404_NOT_FOUND)


class UserListView(generics.ListAPIView):
    """
    List all users (for admin/manager use)
    """
    queryset = User.objects.all().select_related('profile')
    serializer_class = UserResponseSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Filter users based on user role
        """
        user = self.request.user
        
        # Only admin and managers can see all users
        try:
            user_profile = UserProfile.objects.get(user=user)
            if user_profile.role in ['admin', 'manager']:
                return User.objects.all().select_related('profile')
            else:
                # Regular users can only see their own data
                return User.objects.filter(id=user.id).select_related('profile')
        except UserProfile.DoesNotExist:
            return User.objects.filter(id=user.id).select_related('profile')


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def check_username_availability(request):
    """
    Check if username is available
    """
    username = request.data.get('username')
    
    if not username:
        return Response({
            'success': False,
            'message': 'Username is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    is_available = not User.objects.filter(username=username).exists()
    
    return Response({
        'success': True,
        'username': username,
        'available': is_available,
        'message': 'Username is available' if is_available else 'Username is already taken'
    })


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def check_email_availability(request):
    """
    Check if email is available
    """
    email = request.data.get('email')
    
    if not email:
        return Response({
            'success': False,
            'message': 'Email is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    is_available = not User.objects.filter(email=email).exists()
    
    return Response({
        'success': True,
        'email': email,
        'available': is_available,
        'message': 'Email is available' if is_available else 'Email is already registered'
    })
