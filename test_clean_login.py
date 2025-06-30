#!/usr/bin/env python
"""
Simple test to verify login works after removing debug lines
"""

import requests

def test_login_simple():
    print("🧪 Testing login functionality...")
    
    # Test with the test user we created
    login_mutation = """
    mutation {
        tokenAuth(username: "testuser", password: "testpass123") {
            token
            user {
                id
                username
                email
                profile {
                    role
                }
            }
        }
    }
    """
    
    response = requests.post(
        'http://localhost:8000/graphql/',
        json={'query': login_mutation}
    )
    
    if response.status_code == 200:
        data = response.json()
        if 'errors' in data:
            print("❌ Login failed:", data['errors'])
            return False
        else:
            print("✅ Login successful!")
            user = data['data']['tokenAuth']['user']
            print(f"   Username: {user['username']}")
            print(f"   Email: {user['email']}")
            print(f"   Role: {user['profile']['role']}")
            return True
    else:
        print(f"❌ Request failed with status {response.status_code}")
        return False

if __name__ == "__main__":
    test_login_simple()
