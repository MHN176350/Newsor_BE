from django.http import JsonResponse
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User
from .models import UserProfile, TextConfiguration
from .serializers import (
    UserRegistrationSerializer, 
    UserResponseSerializer,
    UserProfileSerializer
)
import json


# Default text configuration
DEFAULT_TEXTS = {
    # Hero Section
    'pageSlogan': 'Innovate together, Succeed Together',
    'pageShortDescription': 'EvoluSoft harnesses cutting-edge technology, collaborating globally with clients to deliver transformative solutions, drive success, and celebrate shared achievements.',
    
    # Company Info
    'companyName': 'EvoluSoft',
    'companyShortDescription1': 'EvoluSoft Co.Ltd is a dynamic IT company dedicated to delivering innovative software solutions that empower customers to succeed.',
    'companyShortDescription2': 'With a team of highly experienced Leaders and technology team including: senior Project mangers, developers, testers, and QA experts, we craft cutting-edge products, especially specialized software\'s for the government sector.',
    'companySloganDescription': 'Guided by our slogan "Collaborate to Celebrate," we partner with customers and global technology vendors to bring world-class solutions to businesses and communities. Our commitment to excellence and innovation drives us to forge strategic alliances with leading international software vendors, ensuring our clients thrive in a transformative digital world.',
    
    # Vision & Mission
    'companyVision1': 'EvoluSoft envisions a world where technology unites people and businesses, driving shared success through seamless collaboration and innovative IT solution.',
    'companyVision2': 'We aim to be a dynamic digital landscape, celebrating transformative achievements together.',
    'companyMission1': 'At EvoluSoft, our mission is to empower customers with innovative IT solution, collaborating closely to drive your success and celebrate shared achievements.',
    'companyMission2': 'By uniting expertise, creativity, and technology, we transform challenges into opportunities for businesses and communities, shaping a brighter digital future.',
    
    # Company Values
    'companyValue1': 'Collaboration: We thrive by partnering with customers and teams, uniting talents to achieve shared goals and celebrate collective success.',
    'companyValue2': 'Innovation: We deliver cutting-edge technology, creating solutions that empower customers to lead and transform.',
    'companyValue3': 'Excellence: We commit to exceptional quality in every project, ensuring outstanding results for our customer.',
    'companyValue4': 'Integrity: We build trust with customers through transparency, honesty, and accountability in all our actions.',
    'companyValue5': 'Customer Success: We prioritize our customers\' triumphs, delivering solutions that drive their growth and prosperity.',
    
    # Services
    'serviceName1': 'Database Services',
    'serviceName2': 'Application Development',
    'serviceName3': 'System Integration',
    
    # Service descriptions and contact info (abbreviated for brevity)
    'contactAddress': '16, BT4-3, Vinaconex 3 - Trung Van, Nam Tu Liem, Hanoi, Vietnam',
    'contactPhone': '(024) 73046618',
    'contactEmail': 'support@evolusoft.vn',
    'workingHoursWeekday': 'Monday - Friday: 8:00 - 17:00',
    'workingHoursWeekend': 'Saturday: 8:00 - 12:00'
}


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


# Text Configuration API Endpoints

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_text_configuration(request):
    """
    Get all text configuration for EvoluSoft homepage
    """
    try:
        # Get all text configurations from database
        text_configs = TextConfiguration.objects.filter(is_active=True)
        
        # Convert to dictionary
        texts = {config.key: config.value for config in text_configs}
        
        # Merge with defaults (in case some keys are missing)
        result = {**DEFAULT_TEXTS, **texts}
        
        return Response({
            'success': True,
            'data': result
        })
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error retrieving text configuration: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])  # TODO: Add proper permissions
def update_text_configuration(request):
    """
    Update text configuration for EvoluSoft homepage
    """
    try:
        texts = request.data
        
        # Update or create each text configuration
        for key, value in texts.items():
            TextConfiguration.objects.update_or_create(
                key=key,
                defaults={
                    'value': value,
                    'is_active': True
                }
            )
        
        return Response({
            'success': True,
            'message': 'Text configuration updated successfully'
        })
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error updating text configuration: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])  # TODO: Add proper permissions
def reset_text_configuration(request):
    """
    Reset text configuration to defaults
    """
    try:
        # Delete all existing configurations
        TextConfiguration.objects.all().delete()
        
        # Create default configurations
        for key, value in DEFAULT_TEXTS.items():
            TextConfiguration.objects.create(
                key=key,
                value=value,
                description=f"Default text for {key}",
                is_active=True
            )
        
        return Response({
            'success': True,
            'message': 'Text configuration reset to defaults'
        })
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error resetting text configuration: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
