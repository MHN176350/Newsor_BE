#!/usr/bin/env python
"""
Check user role and update if needed
"""

import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'newsor.settings')
django.setup()

from django.contrib.auth.models import User
from api.models import UserProfile

def check_and_update_user():
    try:
        user = User.objects.get(username='testuser')
        profile = UserProfile.objects.get(user=user)
        
        print(f"Current user: {user.username}")
        print(f"Current role: {profile.role}")
        
        # Check if user can create articles
        can_create = profile.role.lower() in ['writer', 'manager', 'admin']
        print(f"Can create articles: {can_create}")
        
        if not can_create:
            print("Updating user role to 'writer'...")
            profile.role = 'writer'
            profile.save()
            print("✅ User role updated to 'writer'")
        else:
            print("✅ User already has permission to create articles")
            
    except User.DoesNotExist:
        print("❌ Test user not found")
    except UserProfile.DoesNotExist:
        print("❌ User profile not found")

if __name__ == "__main__":
    check_and_update_user()
