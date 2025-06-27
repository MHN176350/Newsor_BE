#!/usr/bin/env python
"""
Test script to debug the change user role mutation
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'newsor.settings')
django.setup()

from django.contrib.auth.models import User
from api.models import UserProfile
from newsor.schema import schema

def test_change_user_role():
    """Test script to debug the change user role mutation"""
    
    print("Testing change user role mutation...")
    
    # Clean up any existing test users
    User.objects.filter(username__in=['testadmin', 'testuser']).delete()
    
    # Create test users
    admin_user = User.objects.create_user(username='testadmin', email='admin@test.com', password='testpass')
    target_user = User.objects.create_user(username='testuser', email='user@test.com', password='testpass')
    
    # Create profiles
    admin_profile = UserProfile.objects.create(user=admin_user, role='ADMIN')
    target_profile = UserProfile.objects.create(user=target_user, role='reader')
    
    print(f"Created admin user: {admin_user.username} with role: {admin_profile.role}")
    print(f"Created target user: {target_user.username} with role: {target_profile.role}")
    
    # Test the mutation
    query = '''
    mutation {
        changeUserRole(userId: %d, newRole: "writer") {
            success
            errors
            user {
                id
                username
                profile {
                    role
                }
            }
        }
    }
    ''' % target_user.id
    
    # Mock request with admin user
    class MockRequest:
        def __init__(self, user):
            self.user = user
    
    class MockInfo:
        def __init__(self, user):
            self.context = MockRequest(user)
    
    # Execute mutation
    print(f"Executing mutation with admin user authenticated: {admin_user.is_authenticated}")
    result = schema.execute(query, context=MockInfo(admin_user))
    
    print("Mutation result:", result.data)
    if result.errors:
        print("Errors:", result.errors)
    
    # Clean up
    User.objects.filter(username__in=['testadmin', 'testuser']).delete()
    print("Test completed and cleaned up.")

if __name__ == "__main__":
    test_change_user_role()
