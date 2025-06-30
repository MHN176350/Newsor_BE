"""
Cloudinary utilities for optimizing URL storage
"""
import re
from django.conf import settings


class CloudinaryUtils:
    """Utility class for handling Cloudinary URLs"""
    
    # Common Cloudinary base URL patterns
    CLOUDINARY_BASE_PATTERNS = [
        r'https://res\.cloudinary\.com/[^/]+/',
        r'http://res\.cloudinary\.com/[^/]+/',
    ]
    
    @classmethod
    def get_cloudinary_base_url(cls):
        """Get the base Cloudinary URL from settings"""
        if hasattr(settings, 'CLOUDINARY_STORAGE') and 'CLOUD_NAME' in settings.CLOUDINARY_STORAGE:
            cloud_name = settings.CLOUDINARY_STORAGE['CLOUD_NAME']
            return f"https://res.cloudinary.com/{cloud_name}/"
        return None
    
    @classmethod
    def strip_base_url(cls, full_url):
        """
        Strip the base Cloudinary URL and return only the resource path
        
        Args:
            full_url (str): Full Cloudinary URL
            
        Returns:
            str: Resource path without base URL, or original URL if no pattern matches
        """
        if not full_url:
            return full_url
            
        for pattern in cls.CLOUDINARY_BASE_PATTERNS:
            match = re.match(pattern, full_url)
            if match:
                return full_url[len(match.group(0)):]
        
        return full_url
    
    @classmethod
    def build_full_url(cls, resource_path):
        """
        Build full Cloudinary URL from resource path
        
        Args:
            resource_path (str): Resource path without base URL
            
        Returns:
            str: Full Cloudinary URL or original path if base URL not available
        """
        if not resource_path:
            return resource_path
            
        # If it's already a full URL, return as is
        if resource_path.startswith(('http://', 'https://')):
            return resource_path
            
        base_url = cls.get_cloudinary_base_url()
        if base_url:
            return f"{base_url}{resource_path}"
        
        return resource_path
    
    @classmethod
    def optimize_for_storage(cls, cloudinary_url):
        """
        Optimize Cloudinary URL for database storage by removing redundant base URL
        
        Args:
            cloudinary_url (str): Full Cloudinary URL
            
        Returns:
            str: Optimized URL for storage (resource path only)
        """
        return cls.strip_base_url(cloudinary_url)
    
    @classmethod
    def restore_for_display(cls, stored_path):
        """
        Restore full Cloudinary URL for display from stored resource path
        
        Args:
            stored_path (str): Stored resource path
            
        Returns:
            str: Full Cloudinary URL for display
        """
        return cls.build_full_url(stored_path)


def process_cloudinary_field_for_storage(value):
    """
    Process a CloudinaryField value before saving to database
    
    Args:
        value: CloudinaryField value (could be string URL or Cloudinary resource)
        
    Returns:
        Optimized value for storage
    """
    if hasattr(value, 'url'):
        # It's a Cloudinary resource object
        return CloudinaryUtils.optimize_for_storage(value.url)
    elif isinstance(value, str):
        # It's a string URL
        return CloudinaryUtils.optimize_for_storage(value)
    
    return value


def process_cloudinary_field_for_display(value):
    """
    Process a stored CloudinaryField value for display
    
    Args:
        value: Stored CloudinaryField value
        
    Returns:
        Full URL for display
    """
    if isinstance(value, str):
        return CloudinaryUtils.restore_for_display(value)
    
    return value
