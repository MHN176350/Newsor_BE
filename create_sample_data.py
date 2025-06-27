#!/usr/bin/env python
"""
Create sample data for testing the frontend
"""
import os
import sys
import django

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'newsor.settings')
django.setup()

from django.contrib.auth.models import User
from api.models import Category, Tag, News, UserProfile
from django.utils import timezone
from django.utils.text import slugify

def create_sample_data():
    """Create sample categories, tags, and news articles"""
    print("Creating sample data...")
    
    # Create categories
    categories_data = [
        {'name': 'Technology', 'description': 'Latest technology news and updates'},
        {'name': 'Sports', 'description': 'Sports news and events'},
        {'name': 'Business', 'description': 'Business and finance news'},
        {'name': 'Health', 'description': 'Health and wellness articles'},
        {'name': 'Entertainment', 'description': 'Entertainment and celebrity news'},
    ]
    
    categories = []
    for cat_data in categories_data:
        category, created = Category.objects.get_or_create(
            name=cat_data['name'],
            defaults={
                'slug': slugify(cat_data['name']),
                'description': cat_data['description']
            }
        )
        categories.append(category)
        if created:
            print(f"✅ Created category: {category.name}")
        else:
            print(f"ℹ️  Category already exists: {category.name}")
    
    # Create tags
    tags_data = ['AI', 'Machine Learning', 'Football', 'Basketball', 'Startup', 'Investment', 'Nutrition', 'Fitness', 'Movies', 'Music']
    tags = []
    for tag_name in tags_data:
        tag, created = Tag.objects.get_or_create(
            name=tag_name,
            defaults={'slug': slugify(tag_name)}
        )
        tags.append(tag)
        if created:
            print(f"✅ Created tag: {tag.name}")
    
    # Get or create author with writer role
    user = User.objects.filter(username='meer').first()
    if user:
        # Ensure user has a profile with writer role
        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={'role': 'writer'}
        )
        if created:
            print(f"✅ Created profile for user: {user.username}")
        elif profile.role == 'reader':
            profile.role = 'writer'
            profile.save()
            print(f"✅ Updated user role to writer: {user.username}")
    else:
        print("❌ User 'meer' not found. Please create a user first.")
        return
    
    # Create news articles
    news_data = [
        {
            'title': 'Revolutionary AI Technology Breakthrough',
            'content': 'Scientists have made a groundbreaking discovery in artificial intelligence that could change the way we interact with computers forever. This new technology promises to make AI more intuitive and human-like than ever before.',
            'excerpt': 'A revolutionary breakthrough in AI technology promises to transform human-computer interaction.',
            'category': categories[0],  # Technology
            'tags': [tags[0], tags[1]],  # AI, Machine Learning
            'status': 'published'
        },
        {
            'title': 'Championship Football Match Results',
            'content': 'Last night\'s championship match was one for the history books. Both teams played their hearts out in what many are calling the game of the century. The final score surprised everyone.',
            'excerpt': 'Historic championship match delivers unexpected results in thrilling conclusion.',
            'category': categories[1],  # Sports
            'tags': [tags[2]],  # Football
            'status': 'published'
        },
        {
            'title': 'New Health Guidelines Released',
            'content': 'Health experts have released new guidelines for maintaining optimal wellness in the modern age. These recommendations focus on nutrition, exercise, and mental health.',
            'excerpt': 'New health guidelines focus on holistic wellness for modern lifestyle.',
            'category': categories[3],  # Health
            'tags': [tags[6], tags[7]],  # Nutrition, Fitness
            'status': 'published'
        },
        {
            'title': 'Startup Funding Reaches Record Highs',
            'content': 'Venture capital investment in startups has reached unprecedented levels this quarter. Technology companies are leading the charge with innovative solutions.',
            'excerpt': 'Record venture capital funding flows to innovative startup companies.',
            'category': categories[2],  # Business
            'tags': [tags[4], tags[5]],  # Startup, Investment
            'status': 'published'
        }
    ]
    
    for news_item in news_data:
        # Create slug from title
        slug = slugify(news_item['title'])
        
        # Ensure slug is unique
        counter = 1
        original_slug = slug
        while News.objects.filter(slug=slug).exists():
            slug = f"{original_slug}-{counter}"
            counter += 1
        
        news, created = News.objects.get_or_create(
            title=news_item['title'],
            defaults={
                'slug': slug,
                'content': news_item['content'],
                'excerpt': news_item['excerpt'],
                'author': user,
                'category': news_item['category'],
                'status': news_item['status'],
                'published_at': timezone.now() if news_item['status'] == 'published' else None
            }
        )
        
        if created:
            # Add tags
            news.tags.set(news_item['tags'])
            print(f"✅ Created news article: {news.title}")
        else:
            print(f"ℹ️  News article already exists: {news.title}")
    
    print("\n🎉 Sample data creation completed!")
    print(f"Categories: {Category.objects.count()}")
    print(f"Tags: {Tag.objects.count()}")
    print(f"News articles: {News.objects.count()}")
    print(f"Published articles: {News.objects.filter(status='published').count()}")

if __name__ == "__main__":
    create_sample_data()
