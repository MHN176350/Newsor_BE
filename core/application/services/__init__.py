"""
Application services for content processing and business logic.
"""

from abc import ABC, abstractmethod
import re
from django.utils.text import slugify


class ContentSanitizationService(ABC):
    """Abstract service for content sanitization."""

    @abstractmethod
    def sanitize(self, content: str) -> str:
        pass


class SlugGenerationService:
    """Service for generating unique slugs."""

    def generate_unique_slug(self, title: str, news_repository) -> str:
        """Generate a unique slug from title."""
        base_slug = slugify(title)
        slug = base_slug
        counter = 1

        while news_repository.get_by_slug(slug):
            slug = f"{base_slug}-{counter}"
            counter += 1

        return slug


class ImageUploadService(ABC):
    """Abstract service for image upload operations."""

    @abstractmethod
    def get_upload_signature(self) -> dict:
        pass

    @abstractmethod
    def extract_image_urls_from_content(self, content: str) -> list:
        pass


class ContentImageExtractorService:
    """Service for extracting image URLs from HTML content."""

    def extract_image_urls(self, content: str) -> list:
        """Extract all image URLs from HTML content."""
        img_pattern = r'<img[^>]+src="([^"]+)"[^>]*>'
        matches = re.findall(img_pattern, content)
        return matches
