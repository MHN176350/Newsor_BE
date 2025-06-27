#!/usr/bin/env python
"""
Test script to check JWT authentication for change user role mutation
"""

import os
import sys
import django
import requests
import json

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'newsor.settings')
django.setup()

from django.contrib.auth.models import User
from api.models import UserProfile

def test_change_role_with_token():
    """Test the change role mutation with proper JWT token"""
    
    # GraphQL endpoint
    url = 'http://localhost:8000/graphql/'
    
    # First, login to get a token
    login_mutation = """
    mutation LoginUser($username: String!, $password: String!) {
        tokenAuth(username: $username, password: $password) {
            token
            refreshToken
            user {
                id
                username
                profile {
                    role
                }
            }
        }
    }
    """
    
    # Login with admin credentials
    login_response = requests.post(url, json={
        'query': login_mutation,
        'variables': {
            'username': 'admin',
            'password': 'admin123'
        }
    })
    
    print("Login response status:", login_response.status_code)
    login_data = login_response.json()
    print("Login response:", json.dumps(login_data, indent=2))
    
    if 'errors' in login_data:
        print("Login failed, errors:", login_data['errors'])
        return
    
    # Extract token
    token = login_data['data']['tokenAuth']['token']
    user_role = login_data['data']['tokenAuth']['user']['profile']['role']
    print(f"Logged in successfully. Token: {token[:20]}... Role: {user_role}")
    
    # Now try the change role mutation
    change_role_mutation = """
    mutation ChangeUserRole($userId: Int!, $newRole: String!) {
        changeUserRole(userId: $userId, newRole: $newRole) {
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
    """
    
    # Try to change a user's role (assuming user ID 2 exists)
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    change_role_response = requests.post(url, 
        headers=headers,
        json={
            'query': change_role_mutation,
            'variables': {
                'userId': 2,  # Change this to an actual user ID
                'newRole': 'writer'
            }
        }
    )
    
    print("Change role response status:", change_role_response.status_code)
    change_role_data = change_role_response.json()
    print("Change role response:", json.dumps(change_role_data, indent=2))

if __name__ == '__main__':
    test_change_role_with_token()
