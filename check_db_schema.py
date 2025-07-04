#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'newsor.settings')
django.setup()

from django.db import connection

def check_avatar_column():
    cursor = connection.cursor()
    try:
        cursor.execute("""
            SELECT column_name, data_type, character_maximum_length 
            FROM information_schema.columns 
            WHERE table_name = 'api_userprofile' AND column_name = 'avatar';
        """)
        result = cursor.fetchall()
        print("Avatar column schema:")
        for row in result:
            print(f"Column: {row[0]}, Type: {row[1]}, Max Length: {row[2]}")
        
        if not result:
            print("Avatar column not found")
            
        # Also check role column in UserProfile table
        cursor.execute("""
            SELECT column_name, data_type, character_maximum_length 
            FROM information_schema.columns 
            WHERE table_name = 'api_userprofile' AND column_name = 'role';
        """)
        result = cursor.fetchall()
        print("\nRole column schema:")
        for row in result:
            print(f"Column: {row[0]}, Type: {row[1]}, Max Length: {row[2]}")
            
        # Also check featured_image in News table
        cursor.execute("""
            SELECT column_name, data_type, character_maximum_length 
            FROM information_schema.columns 
            WHERE table_name = 'api_news' AND column_name = 'featured_image';
        """)
        result = cursor.fetchall()
        print("\nFeatured image column schema:")
        for row in result:
            print(f"Column: {row[0]}, Type: {row[1]}, Max Length: {row[2]}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cursor.close()

def check_user_roles():
    cursor = connection.cursor()
    try:
        cursor.execute("""
            SELECT u.username, up.role, up.created_at
            FROM auth_user u 
            JOIN api_userprofile up ON u.id = up.user_id
            ORDER BY up.role, u.username;
        """)
        result = cursor.fetchall()
        print("\nCurrent user roles:")
        print("-" * 50)
        for row in result:
            print(f"User: {row[0]:<15} | Role: {row[1]:<10} | Created: {row[2]}")
            
        # Count by role
        cursor.execute("""
            SELECT role, COUNT(*) as count
            FROM api_userprofile
            GROUP BY role
            ORDER BY role;
        """)
        result = cursor.fetchall()
        print("\nRole distribution:")
        print("-" * 30)
        for row in result:
            print(f"{row[0]:<10}: {row[1]} users")
            
    except Exception as e:
        print(f"Error checking user roles: {e}")
    finally:
        cursor.close()

if __name__ == "__main__":
    check_avatar_column()
    check_user_roles()
    check_user_roles()
