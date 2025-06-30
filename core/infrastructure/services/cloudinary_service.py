"""
Infrastructure services implementation.
"""

import bleach
import re
from urllib.parse import urlparse
from django.conf import settings
import cloudinary.utils

from ...application.services import ContentSanitizationService, ImageUploadService


class BleachContentSanitizationService(ContentSanitizationService):
    """Bleach implementation of content sanitization."""

    def sanitize(self, content: str) -> str:
        """Sanitize HTML content to allow only safe tags and attributes."""
        allowed_tags = [
            'p', 'br', 'strong', 'b', 'em', 'i', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'ul', 'ol', 'li', 'blockquote', 'a', 'img', 'div', 'span'
        ]
        
        allowed_attributes = {
            'a': ['href', 'title'],
            'img': ['src', 'alt', 'title', 'width', 'height'],
            'div': ['class'],
            'span': ['class'],
        }
        
        allowed_protocols = ['http', 'https', 'data']
        
        # Sanitize the HTML
        clean_content = bleach.clean(
            content,
            tags=allowed_tags,
            attributes=allowed_attributes,
            protocols=allowed_protocols,
            strip=True
        )
        
        return clean_content


class CloudinaryImageUploadService(ImageUploadService):
    """Cloudinary implementation of image upload service."""

    def get_upload_signature(self) -> dict:
        """Generate a signature for secure Cloudinary uploads."""
        timestamp = cloudinary.utils.now()
        
        params = {
            'timestamp': timestamp,
            'folder': 'news_articles',
            'resource_type': 'image'
        }
        
        signature = cloudinary.utils.api_sign_request(
            params, 
            settings.CLOUDINARY_STORAGE['API_SECRET']
        )
        
        return {
            'signature': signature,
            'timestamp': timestamp,
            'api_key': settings.CLOUDINARY_STORAGE['API_KEY'],
            'cloud_name': settings.CLOUDINARY_STORAGE['CLOUD_NAME'],
            'folder': 'news_articles'
        }

    def extract_image_urls_from_content(self, content: str) -> list:
        """Extract all image URLs from HTML content."""
        img_pattern = r'<img[^>]+src="([^"]+)"[^>]*>'
        matches = re.findall(img_pattern, content)
        return matches
