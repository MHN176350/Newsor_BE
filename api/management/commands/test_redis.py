"""
Django management command to test Redis connection and cache functionality.
"""
from django.core.management.base import BaseCommand
from django.core.cache import caches
from django.conf import settings
import redis
import json
from datetime import datetime


class Command(BaseCommand):
    help = 'Test Redis connection and cache functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--full-test',
            action='store_true',
            help='Run comprehensive cache tests',
        )
        parser.add_argument(
            '--clear-cache',
            action='store_true',
            help='Clear all cache data',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔍 Testing Redis Connection and Cache Functionality'))
        self.stdout.write('=' * 60)
        
        # Test basic Redis connection
        self.test_redis_connection()
        
        # Test Django cache backends
        self.test_django_caches()
        
        if options['clear_cache']:
            self.clear_all_caches()
        
        if options['full_test']:
            self.run_comprehensive_tests()
        
        self.stdout.write(self.style.SUCCESS('\n✅ Redis testing completed!'))

    def test_redis_connection(self):
        """Test direct Redis connection."""
        self.stdout.write('\n📡 Testing Direct Redis Connection...')
        
        try:
            # Parse Redis URL from settings
            redis_url = getattr(settings, 'CHANNEL_LAYERS', {}).get('default', {}).get('CONFIG', {}).get('hosts', ['redis://127.0.0.1:6379/0'])[0]
            
            # Connect to Redis
            r = redis.from_url(redis_url)
            
            # Test basic operations
            r.ping()
            self.stdout.write(self.style.SUCCESS('  ✅ Redis connection successful'))
            
            # Get Redis info
            info = r.info()
            self.stdout.write(f"  📊 Redis version: {info.get('redis_version', 'Unknown')}")
            self.stdout.write(f"  💾 Used memory: {info.get('used_memory_human', 'Unknown')}")
            self.stdout.write(f"  🔗 Connected clients: {info.get('connected_clients', 'Unknown')}")
            
            # Test set/get
            test_key = 'redis_test_key'
            test_value = f'Redis test at {datetime.now()}'
            r.set(test_key, test_value, ex=60)
            retrieved_value = r.get(test_key)
            
            if retrieved_value and retrieved_value.decode() == test_value:
                self.stdout.write(self.style.SUCCESS('  ✅ Redis set/get operations working'))
                r.delete(test_key)
            else:
                self.stdout.write(self.style.ERROR('  ❌ Redis set/get operations failed'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Redis connection failed: {e}'))

    def test_django_caches(self):
        """Test Django cache backends."""
        self.stdout.write('\n🗄️  Testing Django Cache Backends...')
        
        cache_aliases = ['default', 'write_back']
        
        for alias in cache_aliases:
            try:
                cache = caches[alias]
                self.stdout.write(f'\n  Testing cache: {alias}')
                
                # Test basic operations
                test_key = f'django_cache_test_{alias}'
                test_data = {
                    'message': f'Cache test for {alias}',
                    'timestamp': datetime.now().isoformat(),
                    'cache_alias': alias
                }
                
                # Set data
                cache.set(test_key, test_data, 60)
                self.stdout.write(f'    ✅ Set operation successful')
                
                # Get data
                retrieved_data = cache.get(test_key)
                if retrieved_data == test_data:
                    self.stdout.write(f'    ✅ Get operation successful')
                else:
                    self.stdout.write(f'    ❌ Get operation failed')
                
                # Test has_key
                if cache.has_key(test_key):
                    self.stdout.write(f'    ✅ has_key operation successful')
                else:
                    self.stdout.write(f'    ❌ has_key operation failed')
                
                # Clean up
                cache.delete(test_key)
                self.stdout.write(f'    ✅ Delete operation successful')
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'    ❌ Cache {alias} test failed: {e}'))

    def run_comprehensive_tests(self):
        """Run comprehensive cache tests."""
        self.stdout.write('\n🔬 Running Comprehensive Cache Tests...')
        
        # Test our custom cache managers
        self.test_news_cache()
        self.test_user_cache()
        self.test_write_back_cache()

    def test_news_cache(self):
        """Test news cache manager."""
        self.stdout.write('\n  📰 Testing News Cache Manager...')
        
        try:
            from core.infrastructure.cache.managers import news_cache
            
            # Test article caching
            test_article = {
                'id': 999,
                'title': 'Test Article',
                'slug': 'test-article',
                'content': 'This is a test article content.',
                'status': 'published',
                'view_count': 100,
                'created_at': datetime.now().isoformat()
            }
            
            # Cache article
            success = news_cache.cache_article(test_article)
            if success:
                self.stdout.write('    ✅ Article caching successful')
            else:
                self.stdout.write('    ❌ Article caching failed')
            
            # Retrieve by ID
            cached_article = news_cache.get_article_by_id(999)
            if cached_article and cached_article['title'] == 'Test Article':
                self.stdout.write('    ✅ Article retrieval by ID successful')
            else:
                self.stdout.write('    ❌ Article retrieval by ID failed')
            
            # Retrieve by slug
            cached_article = news_cache.get_article_by_slug('test-article')
            if cached_article and cached_article['title'] == 'Test Article':
                self.stdout.write('    ✅ Article retrieval by slug successful')
            else:
                self.stdout.write('    ❌ Article retrieval by slug failed')
            
            # Test view count increment
            news_cache.queue_view_count_increment(999)
            self.stdout.write('    ✅ View count increment queued')
            
            # Clean up
            news_cache.invalidate_article(999, 'test-article')
            self.stdout.write('    ✅ Article cache invalidated')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'    ❌ News cache test failed: {e}'))

    def test_user_cache(self):
        """Test user cache manager."""
        self.stdout.write('\n  👤 Testing User Cache Manager...')
        
        try:
            from core.infrastructure.cache.managers import user_cache
            
            # Test user caching
            test_user = {
                'id': 999,
                'username': 'testuser',
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User',
                'is_active': True,
                'role': 'writer'
            }
            
            # Cache user
            success = user_cache.cache_user(test_user)
            if success:
                self.stdout.write('    ✅ User caching successful')
            
            # Retrieve by ID
            cached_user = user_cache.get_user_by_id(999)
            if cached_user and cached_user['username'] == 'testuser':
                self.stdout.write('    ✅ User retrieval by ID successful')
            
            # Test permissions caching
            test_permissions = {
                'role': 'writer',
                'can_create_articles': True,
                'can_review_articles': False
            }
            user_cache.cache_user_permissions(999, test_permissions)
            
            cached_permissions = user_cache.get_user_permissions(999)
            if cached_permissions and cached_permissions['role'] == 'writer':
                self.stdout.write('    ✅ User permissions caching successful')
            
            # Clean up
            user_cache.invalidate_user(999, 'testuser')
            self.stdout.write('    ✅ User cache invalidated')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'    ❌ User cache test failed: {e}'))

    def test_write_back_cache(self):
        """Test write-back cache functionality."""
        self.stdout.write('\n  🔄 Testing Write-Back Cache...')
        
        try:
            from core.infrastructure.cache.base import WriteBackCache
            
            write_back = WriteBackCache()
            
            # Queue test operations
            test_data = {
                'title': 'Updated Article Title',
                'content': 'Updated content',
                'updated_at': datetime.now().isoformat()
            }
            
            success = write_back.queue_write('update', 'News', '999', test_data)
            if success:
                self.stdout.write('    ✅ Write operation queued successfully')
            
            # Get pending operations
            pending = write_back.get_pending_operations('News')
            if pending:
                self.stdout.write(f'    ✅ Found {len(pending)} pending operations')
            
            # Clear test operations
            write_back.clear_pending_operations('News')
            self.stdout.write('    ✅ Test operations cleared')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'    ❌ Write-back cache test failed: {e}'))

    def clear_all_caches(self):
        """Clear all cache data."""
        self.stdout.write('\n🧹 Clearing All Cache Data...')
        
        try:
            # Clear Django caches
            for alias in ['default', 'write_back']:
                try:
                    cache = caches[alias]
                    cache.clear()
                    self.stdout.write(f'  ✅ Cleared {alias} cache')
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'  ⚠️  Could not clear {alias} cache: {e}'))
            
            self.stdout.write(self.style.SUCCESS('✅ All caches cleared'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error clearing caches: {e}'))

    def get_cache_stats(self):
        """Get cache statistics."""
        self.stdout.write('\n📊 Cache Statistics...')
        
        try:
            # Get Redis info
            redis_url = getattr(settings, 'CHANNEL_LAYERS', {}).get('default', {}).get('CONFIG', {}).get('hosts', ['redis://127.0.0.1:6379/0'])[0]
            r = redis.from_url(redis_url)
            
            info = r.info()
            self.stdout.write(f'  📊 Redis Memory Usage: {info.get("used_memory_human", "Unknown")}')
            self.stdout.write(f'  🔑 Total Keys: {r.dbsize()}')
            self.stdout.write(f'  👥 Connected Clients: {info.get("connected_clients", "Unknown")}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Could not get cache stats: {e}'))
