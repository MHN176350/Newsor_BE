# Add these URLs to your api/urls.py

from django.urls import path
from . import views_image

urlpatterns = [
    # ... your existing URLs ...
    
    # Image upload endpoints
    path('upload-image/', views_image.upload_image, name='upload_image'),
    path('register-with-avatar/', views_image.register_user_with_avatar, name='register_with_avatar'),
]
