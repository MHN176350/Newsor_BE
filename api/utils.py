import bleach
import re
from urllib.parse import urlparse
from django.conf import settings


def sanitize_html_content(content):
    """
    Sanitize HTML content to allow only safe tags and attributes
    """
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
    
    # Only allow images from Cloudinary or data URLs
    def is_allowed_image_src(tag, name, value):
        if name == 'src' and tag == 'img':
            parsed = urlparse(value)
            # Allow Cloudinary URLs and data URLs
            return (
                parsed.netloc.endswith('cloudinary.com') or 
                value.startswith('data:image/') or
                parsed.netloc in settings.ALLOWED_IMAGE_DOMAINS if hasattr(settings, 'ALLOWED_IMAGE_DOMAINS') else False
            )
        return True
    
    # Sanitize the HTML
    clean_content = bleach.clean(
        content,
        tags=allowed_tags,
        attributes=allowed_attributes,
        protocols=allowed_protocols,
        strip=True
    )
    
    return clean_content


def get_cloudinary_upload_signature():
    """
    Generate a signature for secure Cloudinary uploads
    """
    import cloudinary.utils
    timestamp = cloudinary.utils.now()
    
    params = {
        'timestamp': timestamp,
        'folder': 'news_articles',
        'resource_type': 'image'
    }
    
    signature = cloudinary.utils.api_sign_request(params, settings.CLOUDINARY_STORAGE['API_SECRET'])
    
    return {
        'signature': signature,
        'timestamp': timestamp,
        'api_key': settings.CLOUDINARY_STORAGE['API_KEY'],
        'cloud_name': settings.CLOUDINARY_STORAGE['CLOUD_NAME'],
        'folder': 'news_articles'
    }


def extract_image_urls_from_content(content):
    """
    Extract all image URLs from HTML content
    """
    img_pattern = r'<img[^>]+src="([^"]+)"[^>]*>'
    matches = re.findall(img_pattern, content)
    return matches
