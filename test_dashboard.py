#!/usr/bin/env python3

import os
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'newsor.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from newsor.schema import schema
from api.models import UserProfile

def test_dashboard_stats():
    factory = RequestFactory()
    request = factory.get('/')
    
    # Create an admin user for testing
    admin_user = User.objects.filter(username='admin').first()
    if not admin_user:
        admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='admin123'
        )
        UserProfile.objects.create(
            user=admin_user,
            role='admin'
        )
    
    request.user = admin_user

    print("Testing dashboard statistics...\n")

    # Test dashboard stats query
    query = """
    query {
        dashboardStats {
            totalUsers
            totalReaders
            totalWriters
            totalManagers
            totalAdmins
            newUsersThisMonth
            totalNews
            publishedNews
            draftNews
            pendingNews
            rejectedNews
            newsThisMonth
            totalCategories
            totalTags
            totalViews
            totalLikes
            totalComments
        }
    }
    """
    
    result = schema.execute(query, context=request)
    
    if result.errors:
        print("GraphQL Errors:")
        for error in result.errors:
            print(f"  - {error}")
    else:
        print("Dashboard Statistics:")
        print(json.dumps(result.data, indent=2))

    # Test recent activity query
    activity_query = """
    query {
        recentActivity(limit: 3) {
            id
            action
            description
            timestamp
            user {
                username
                firstName
                lastName
            }
        }
    }
    """
    
    activity_result = schema.execute(activity_query, context=request)
    
    if activity_result.errors:
        print("\nRecent Activity Errors:")
        for error in activity_result.errors:
            print(f"  - {error}")
    else:
        print("\nRecent Activity:")
        print(json.dumps(activity_result.data, indent=2))

if __name__ == "__main__":
    test_dashboard_stats()
