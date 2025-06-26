from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import UserProfile
import cloudinary.uploader
import uuid


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration
    """
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        help_text="Password must be at least 8 characters long"
    )
    password_confirm = serializers.CharField(
        write_only=True,
        help_text="Confirm your password"
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password_confirm', 'first_name', 'last_name')
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': False},
            'last_name': {'required': False},
        }

    def validate_email(self, value):
        """
        Validate that email is unique
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_username(self, value):
        """
        Validate that username is unique
        """
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def validate(self, attrs):
        """
        Validate password confirmation and strength
        """
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')
        
        # Check password confirmation
        if password != password_confirm:
            raise serializers.ValidationError({
                'password_confirm': 'Password confirmation does not match.'
            })
        
        # Use Django's password validation
        try:
            validate_password(password)
        except ValidationError as e:
            raise serializers.ValidationError({
                'password': list(e.messages)
            })
        
        return attrs

    def create(self, validated_data):
        """
        Create new user and profile
        """
        # Remove password_confirm from validated_data
        validated_data.pop('password_confirm', None)
        
        # Create user
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        
        # Create user profile with reader role
        UserProfile.objects.create(
            user=user,
            role='reader',
            is_verified=False
        )
        
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile information
    """
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    full_name = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'bio', 'avatar', 'avatar_url', 'phone', 'date_of_birth', 
            'is_verified', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'role', 'is_verified', 'created_at', 'updated_at')

    def get_full_name(self, obj):
        """
        Get user's full name
        """
        return f"{obj.user.first_name} {obj.user.last_name}".strip()

    def get_avatar_url(self, obj):
        """
        Get avatar URL from Cloudinary field
        """
        if obj.avatar:
            try:
                return str(obj.avatar.url)
            except Exception:
                return "/static/images/default-avatar.svg"
        return "/static/images/default-avatar.svg"


class UserResponseSerializer(serializers.ModelSerializer):
    """
    Serializer for user response after registration
    """
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'date_joined', 'profile')
        read_only_fields = ('id', 'date_joined')


class ImageUploadSerializer(serializers.Serializer):
    """
    Serializer for image upload to Cloudinary
    """
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

class UserRegistrationWithAvatarSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration with avatar
    """
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
