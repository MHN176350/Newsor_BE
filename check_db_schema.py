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

if __name__ == "__main__":
    check_avatar_column()
