from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import views_image

# Create router for API endpoints
router = DefaultRouter()

urlpatterns = [
    # Health check
    path('health/', views.health_check, name='health_check'),
    
    # User registration and authentication
    path('auth/register/', views.UserRegistrationView.as_view(), name='user_register'),
    path('auth/profile/', views.user_profile_view, name='user_profile'),
    path('auth/profile/update/', views.update_profile_view, name='update_profile'),
    
    # User management
    path('users/', views.UserListView.as_view(), name='user_list'),
    
    # Utility endpoints
    path('utils/check-username/', views.check_username_availability, name='check_username'),
    path('utils/check-email/', views.check_email_availability, name='check_email'),
    
    # Image upload endpoints
    path('upload-image/', views_image.upload_image, name='upload_image'),
    path('register-with-avatar/', views_image.register_user_with_avatar, name='register_with_avatar'),
    
    # Text Configuration endpoints
    path('text-config/', views.get_text_configuration, name='get_text_config'),
    path('text-config/update/', views.update_text_configuration, name='update_text_config'),
    path('text-config/reset/', views.reset_text_configuration, name='reset_text_config'),
    
    # Include router URLs
    path('', include(router.urls)),
]
