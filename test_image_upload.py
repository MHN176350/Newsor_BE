#!/usr/bin/env python3
"""
Test script for base64 image upload functionality
"""
import base64
import requests
import json
from pathlib import Path

# Test data - create a simple 1x1 pixel PNG in base64
TEST_IMAGE_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

def test_base64_upload():
    """Test the base64 image upload GraphQL mutation"""
    
    # GraphQL endpoint
    url = "http://127.0.0.1:8000/graphql/"
    
    # GraphQL mutation
    mutation = """
    mutation UploadBase64Image($base64Data: String!) {
        uploadBase64Image(base64Data: $base64Data) {
            url
            publicId
            success
            errors
        }
    }
    """
    
    # Request payload
    payload = {
        "query": mutation,
        "variables": {
            "base64Data": f"data:image/png;base64,{TEST_IMAGE_BASE64}"
        }
    }
    
    # Headers
    headers = {
        "Content-Type": "application/json",
    }
    
    try:
        # Make the request
        response = requests.post(url, json=payload, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data and data["data"]["uploadBase64Image"]["success"]:
                print("✅ Base64 image upload test PASSED")
                print(f"Uploaded URL: {data['data']['uploadBase64Image']['url']}")
                return True
            else:
                print("❌ Base64 image upload test FAILED")
                print(f"Errors: {data.get('data', {}).get('uploadBase64Image', {}).get('errors', [])}")
        else:
            print("❌ HTTP request failed")
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
    
    return False

def test_graphql_schema():
    """Test if the GraphQL schema includes our new mutations"""
    
    url = "http://127.0.0.1:8000/graphql/"
    
    # Introspection query to check available mutations
    query = """
    query IntrospectionQuery {
        __schema {
            mutationType {
                fields {
                    name
                    description
                }
            }
        }
    }
    """
    
    payload = {
        "query": query
    }
    
    headers = {
        "Content-Type": "application/json",
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            mutations = data.get("data", {}).get("__schema", {}).get("mutationType", {}).get("fields", [])
            
            mutation_names = [field["name"] for field in mutations]
            
            print("Available mutations:")
            for name in sorted(mutation_names):
                print(f"  - {name}")
            
            # Check for our new mutations
            required_mutations = ["uploadBase64Image", "uploadAvatarImage"]
            missing_mutations = [m for m in required_mutations if m not in mutation_names]
            
            if not missing_mutations:
                print("✅ All required mutations are available")
                return True
            else:
                print(f"❌ Missing mutations: {missing_mutations}")
        else:
            print(f"❌ Schema introspection failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Schema test failed: {e}")
    
    return False

if __name__ == "__main__":
    print("Testing GraphQL Image Upload Functionality")
    print("=" * 50)
    
    print("\n1. Testing GraphQL Schema...")
    schema_ok = test_graphql_schema()
    
    print("\n2. Testing Base64 Image Upload...")
    upload_ok = test_base64_upload()
    
    print("\n" + "=" * 50)
    if schema_ok and upload_ok:
        print("🎉 All tests PASSED!")
    else:
        print("❌ Some tests FAILED!")
