# Add this to your existing serializers.py in the api app

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile
import cloudinary.uploader
import uuid

class ImageUploadSerializer(serializers.Serializer):
    image = serializers.ImageField()
    
    def create(self, validated_data):
        image = validated_data['image']
        
        # Generate unique filename
        unique_filename = f"profile_{uuid.uuid4().hex}"
        
        # Upload to Cloudinary
        try:
            upload_result = cloudinary.uploader.upload(
                image,
                public_id=unique_filename,
                folder="newsor/profiles",
                transformation=[
                    {'width': 400, 'height': 400, 'crop': 'fill'},
                    {'quality': 'auto'},
                    {'fetch_format': 'auto'}
                ]
            )
            return {
                'url': upload_result['secure_url'],
                'public_id': upload_result['public_id']
            }
        except Exception as e:
            raise serializers.ValidationError(f"Image upload failed: {str(e)}")

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    avatar = serializers.URLField(required=False, allow_blank=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'confirm_password', 'avatar']
    
    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords don't match.")
        return data
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        avatar_url = validated_data.pop('avatar', '')
        
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            password=validated_data['password']
        )
        
        # Create or update user profile with avatar
        profile, created = UserProfile.objects.get_or_create(user=user)
        if avatar_url:
            profile.avatar = avatar_url
            profile.save()
        
        return user
