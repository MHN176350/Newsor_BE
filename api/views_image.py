# Add these views to your existing views.py in the api app

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from .serializers import UserRegistrationWithAvatarSerializer, ImageUploadSerializer
import json

@api_view(['POST'])
@permission_classes([AllowAny])
def upload_image(request):
    """
    Upload image to Cloudinary and return the URL
    """
    serializer = ImageUploadSerializer(data=request.data)
    if serializer.is_valid():
        try:
            result = serializer.save()
            return Response({
                'success': True,
                'url': result['url'],
                'public_id': result['public_id']
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user_with_avatar(request):
    """
    Register user with optional avatar
    """
    serializer = UserRegistrationWithAvatarSerializer(data=request.data)
    if serializer.is_valid():
        try:
            user = serializer.save()
            return Response({
                'success': True,
                'message': 'User registered successfully',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'avatar': user.userprofile.avatar if hasattr(user, 'userprofile') else None
                }
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)
