#!/usr/bin/env python
import os
import django
import json

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'newsor.settings')
django.setup()

from graphene.test import Client
from api.schema import schema
from django.contrib.auth.models import User
from api.models import UserProfile

# Create a test admin user for testing
try:
    user = User.objects.get(username='admin')
except User.DoesNotExist:
    user = User.objects.create_superuser('admin', 'admin@test.com', 'admin123')
    
# Make sure user has profile
profile, created = UserProfile.objects.get_or_create(
    user=user,
    defaults={'role': 'admin'}
)

# Create GraphQL client
client = Client(schema)

# Test the emailTemplates query (camelCase)
query1 = '''
query {
    emailTemplates {
        id
        name
        subject
        content
    }
}
'''

print("Testing camelCase query: emailTemplates")
result1 = client.execute(query1, context_value={'user': user})
print("Result:", json.dumps(result1, indent=2))

print("\n" + "="*50 + "\n")

# Test the email_templates query (snake_case)
query2 = '''
query {
    email_templates {
        id
        name
        subject
        content
    }
}
'''

print("Testing snake_case query: email_templates")  
result2 = client.execute(query2, context_value={'user': user})
print("Result:", json.dumps(result2, indent=2))
