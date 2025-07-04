"""
Dependency injection container for Clean Architecture.
This centralizes the creation and wiring of dependencies.
"""

from .core.application.use_cases.news_use_cases import (
    CreateNewsUseCase, GetPublishedNewsUseCase, GetNewsBySlugUseCase, UpdateNewsStatusUseCase
)
from .core.infrastructure.repositories.django_repositories import (
    DjangoNewsRepository, DjangoUserProfileRepository, 
    DjangoCategoryRepository, DjangoTagRepository
)
from .core.infrastructure.services.cloudinary_service import (
    BleachContentSanitizationService, CloudinaryImageUploadService
)
from .core.application.services import SlugGenerationService


class DIContainer:
    """Dependency Injection Container."""
    
    def __init__(self):
        self._instances = {}
    
    def get_news_repository(self):
        if 'news_repository' not in self._instances:
            self._instances['news_repository'] = DjangoNewsRepository()
        return self._instances['news_repository']
    
    def get_user_profile_repository(self):
        if 'user_profile_repository' not in self._instances:
            self._instances['user_profile_repository'] = DjangoUserProfileRepository()
        return self._instances['user_profile_repository']
    
    def get_category_repository(self):
        if 'category_repository' not in self._instances:
            self._instances['category_repository'] = DjangoCategoryRepository()
        return self._instances['category_repository']
    
    def get_tag_repository(self):
        if 'tag_repository' not in self._instances:
            self._instances['tag_repository'] = DjangoTagRepository()
        return self._instances['tag_repository']
    
    def get_content_sanitization_service(self):
        if 'content_sanitization_service' not in self._instances:
            self._instances['content_sanitization_service'] = BleachContentSanitizationService()
        return self._instances['content_sanitization_service']
    
    def get_slug_generation_service(self):
        if 'slug_generation_service' not in self._instances:
            self._instances['slug_generation_service'] = SlugGenerationService()
        return self._instances['slug_generation_service']
    
    def get_image_upload_service(self):
        if 'image_upload_service' not in self._instances:
            self._instances['image_upload_service'] = CloudinaryImageUploadService()
        return self._instances['image_upload_service']
    
    def get_create_news_use_case(self):
        if 'create_news_use_case' not in self._instances:
            self._instances['create_news_use_case'] = CreateNewsUseCase(
                news_repository=self.get_news_repository(),
                user_profile_repository=self.get_user_profile_repository(),
                category_repository=self.get_category_repository(),
                tag_repository=self.get_tag_repository(),
                content_sanitization_service=self.get_content_sanitization_service(),
                slug_generation_service=self.get_slug_generation_service(),
            )
        return self._instances['create_news_use_case']
    
    def get_published_news_use_case(self):
        if 'published_news_use_case' not in self._instances:
            self._instances['published_news_use_case'] = GetPublishedNewsUseCase(
                news_repository=self.get_news_repository()
            )
        return self._instances['published_news_use_case']
    
    def get_news_by_slug_use_case(self):
        if 'news_by_slug_use_case' not in self._instances:
            self._instances['news_by_slug_use_case'] = GetNewsBySlugUseCase(
                news_repository=self.get_news_repository()
            )
        return self._instances['news_by_slug_use_case']
    
    def get_update_news_status_use_case(self):
        if 'update_news_status_use_case' not in self._instances:
            self._instances['update_news_status_use_case'] = UpdateNewsStatusUseCase(
                news_repository=self.get_news_repository(),
                user_profile_repository=self.get_user_profile_repository(),
            )
        return self._instances['update_news_status_use_case']


# Global container instance
container = DIContainer()
