#!/usr/bin/env python3
"""
Test Cloudinary signature generation
"""
import os
import sys
import django

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'newsor.settings')
django.setup()

import cloudinary
import cloudinary.utils
from django.conf import settings
import json

def test_signature_generation():
    """Test signature generation"""
    print("=== Testing Cloudinary Signature Generation ===")
    
    # Check config
    print(f"Cloud Name: {settings.CLOUDINARY_STORAGE['CLOUD_NAME']}")
    print(f"API Key: {settings.CLOUDINARY_STORAGE['API_KEY']}")
    print(f"API Secret: {'***' if settings.CLOUDINARY_STORAGE['API_SECRET'] else 'NOT SET'}")
    
    # Test timestamp
    timestamp = cloudinary.utils.now()
    print(f"Timestamp: {timestamp}")
    
    # Test different parameter combinations
    print("\n=== Method 1: Current implementation ===")
    params1 = {
        'timestamp': timestamp,
        'folder': 'news_articles',
        'resource_type': 'image'
    }
    
    signature1 = cloudinary.utils.api_sign_request(params1, settings.CLOUDINARY_STORAGE['API_SECRET'])
    print(f"Params: {params1}")
    print(f"Signature: {signature1}")
    
    print("\n=== Method 2: Minimal params ===")
    params2 = {
        'timestamp': timestamp,
    }
    
    signature2 = cloudinary.utils.api_sign_request(params2, settings.CLOUDINARY_STORAGE['API_SECRET'])
    print(f"Params: {params2}")
    print(f"Signature: {signature2}")
    
    print("\n=== Method 3: With upload preset ===")
    params3 = {
        'timestamp': timestamp,
        'upload_preset': 'news_upload'
    }
    
    signature3 = cloudinary.utils.api_sign_request(params3, settings.CLOUDINARY_STORAGE['API_SECRET'])
    print(f"Params: {params3}")
    print(f"Signature: {signature3}")
    
    print("\n=== Method 4: Standard upload params ===")
    params4 = {
        'timestamp': timestamp,
        'folder': 'news_articles'
    }
    
    signature4 = cloudinary.utils.api_sign_request(params4, settings.CLOUDINARY_STORAGE['API_SECRET'])
    print(f"Params: {params4}")
    print(f"Signature: {signature4}")
    
    print("\n=== Testing actual upload ===")
    try:
        # Create a test image data (1x1 pixel PNG)
        test_image_data = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        
        # Try uploading with our signature
        upload_result = cloudinary.uploader.upload(
            test_image_data,
            folder="news_articles",
            timestamp=timestamp,
            signature=signature4,
            api_key=settings.CLOUDINARY_STORAGE['API_KEY']
        )
        
        print(f"Upload successful: {upload_result.get('public_id')}")
        
    except Exception as e:
        print(f"Upload failed: {str(e)}")
        
        # Try with cloudinary's built-in method
        try:
            upload_result = cloudinary.uploader.upload(
                test_image_data,
                folder="news_articles"
            )
            print(f"Direct upload successful: {upload_result.get('public_id')}")
        except Exception as e2:
            print(f"Direct upload also failed: {str(e2)}")

if __name__ == "__main__":
    test_signature_generation()
