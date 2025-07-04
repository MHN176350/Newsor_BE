"""
Application use cases for news management.
These contain the business logic and orchestrate domain entities.
"""

from typing import List, Optional
from ..domain.entities import News, NewsStatus, UserRole
from ..domain.repositories import NewsRepository, UserProfileRepository, CategoryRepository, TagRepository
from .services import ContentSanitizationService, SlugGenerationService


class CreateNewsUseCase:
    """Use case for creating a new news article."""

    def __init__(
        self,
        news_repository: NewsRepository,
        user_profile_repository: UserProfileRepository,
        category_repository: CategoryRepository,
        tag_repository: TagRepository,
        content_sanitization_service: ContentSanitizationService,
        slug_generation_service: SlugGenerationService,
    ):
        self.news_repository = news_repository
        self.user_profile_repository = user_profile_repository
        self.category_repository = category_repository
        self.tag_repository = tag_repository
        self.content_sanitization_service = content_sanitization_service
        self.slug_generation_service = slug_generation_service

    def execute(self, news: News, author_id: int) -> News:
        """Execute the create news use case."""
        # Validate author permissions
        author_profile = self.user_profile_repository.get_by_user_id(author_id)
        if not author_profile or author_profile.role not in [UserRole.WRITER, UserRole.MANAGER, UserRole.ADMIN]:
            raise PermissionError("User does not have permission to create articles")

        # Validate category exists
        category = self.category_repository.get_by_id(news.category_id)
        if not category:
            raise ValueError("Category not found")

        # Validate tags exist
        if news.tag_ids:
            tags = self.tag_repository.get_by_ids(news.tag_ids)
            if len(tags) != len(news.tag_ids):
                raise ValueError("One or more tags not found")

        # Sanitize content
        news.content = self.content_sanitization_service.sanitize(news.content)

        # Generate unique slug
        news.slug = self.slug_generation_service.generate_unique_slug(
            news.title, self.news_repository
        )

        # Set author and default status
        news.author_id = author_id
        news.status = NewsStatus.DRAFT

        return self.news_repository.create(news)


class GetPublishedNewsUseCase:
    """Use case for retrieving published news articles."""

    def __init__(self, news_repository: NewsRepository):
        self.news_repository = news_repository

    def execute(self, filters: dict = None) -> List[News]:
        """Execute the get published news use case."""
        return self.news_repository.get_published(filters)


class GetNewsBySlugUseCase:
    """Use case for retrieving news by slug."""

    def __init__(self, news_repository: NewsRepository):
        self.news_repository = news_repository

    def execute(self, slug: str) -> Optional[News]:
        """Execute the get news by slug use case."""
        return self.news_repository.get_by_slug(slug)


class UpdateNewsStatusUseCase:
    """Use case for updating news status (approve, reject, publish)."""

    def __init__(
        self,
        news_repository: NewsRepository,
        user_profile_repository: UserProfileRepository,
    ):
        self.news_repository = news_repository
        self.user_profile_repository = user_profile_repository

    def execute(self, news_id: int, new_status: NewsStatus, user_id: int, review_notes: str = "") -> News:
        """Execute the update news status use case."""
        # Get the news article
        news = self.news_repository.get_by_id(news_id)
        if not news:
            raise ValueError("News article not found")

        # Check user permissions
        user_profile = self.user_profile_repository.get_by_user_id(user_id)
        if not user_profile:
            raise ValueError("User profile not found")

        # Check if user can change status
        if new_status in [NewsStatus.APPROVED, NewsStatus.REJECTED, NewsStatus.PUBLISHED]:
            if user_profile.role not in [UserRole.MANAGER, UserRole.ADMIN]:
                raise PermissionError("User does not have permission to change article status")

        # Update news status
        news.status = new_status
        news.reviewed_by_id = user_id
        news.review_notes = review_notes

        if new_status == NewsStatus.PUBLISHED:
            from datetime import datetime
            news.published_at = datetime.now()

        return self.news_repository.update(news)
