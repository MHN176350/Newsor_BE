"""
Django management command to setup and test Redis cache.
"""
from django.core.management.base import BaseCommand
from core.infrastructure.cache.redis_config import redis_manager, ensure_redis_connection, setup_redis_monitoring
from core.infrastructure.cache.decorators import preload_essential_data
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Setup and test Redis cache system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test',
            action='store_true',
            help='Test Redis connections',
        )
        parser.add_argument(
            '--info',
            action='store_true',
            help='Show Redis information and statistics',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all caches',
        )
        parser.add_argument(
            '--preload',
            action='store_true',
            help='Preload essential data into cache',
        )
        parser.add_argument(
            '--monitor',
            action='store_true',
            help='Setup Redis monitoring',
        )

    def handle(self, *args, **options):
        if options.get('test'):
            self.test_redis()
        elif options.get('info'):
            self.show_redis_info()
        elif options.get('clear'):
            self.clear_caches()
        elif options.get('preload'):
            self.preload_cache()
        elif options.get('monitor'):
            self.setup_monitoring()
        else:
            self.stdout.write("Use --help to see available options")

    def test_redis(self):
        """Test Redis connections."""
        self.stdout.write("Testing Redis connections...")
        
        if ensure_redis_connection():
            self.stdout.write(self.style.SUCCESS('✅ Redis connections working properly'))
        else:
            self.stdout.write(self.style.ERROR('❌ Redis connection test failed'))
            self.stdout.write("Make sure Redis is installed and running:")
            self.stdout.write("  Windows: Download from https://github.com/microsoftarchive/redis/releases")
            self.stdout.write("  Or use Docker: docker run -d -p 6379:6379 redis:alpine")

    def show_redis_info(self):
        """Show Redis information."""
        self.stdout.write("Redis Information:")
        self.stdout.write("-" * 50)
        
        try:
            info = redis_manager.get_cache_info()
            
            if info:
                self.stdout.write(f"Redis Version: {info.get('redis_version', 'unknown')}")
                self.stdout.write(f"Memory Usage: {info.get('used_memory', 'unknown')}")
                self.stdout.write(f"Connected Clients: {info.get('connected_clients', 'unknown')}")
                self.stdout.write(f"Total Commands: {info.get('total_commands_processed', 'unknown')}")
                self.stdout.write(f"Cache Hit Ratio: {info.get('hit_ratio', 0):.2f}%")
            else:
                self.stdout.write(self.style.WARNING("Could not retrieve Redis information"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error getting Redis info: {e}"))

    def clear_caches(self):
        """Clear all caches."""
        self.stdout.write("Clearing all caches...")
        
        if redis_manager.clear_all_caches():
            self.stdout.write(self.style.SUCCESS('✅ All caches cleared successfully'))
        else:
            self.stdout.write(self.style.ERROR('❌ Error clearing caches'))

    def preload_cache(self):
        """Preload essential data into cache."""
        self.stdout.write("Preloading essential data into cache...")
        
        try:
            success = preload_essential_data()
            if success:
                self.stdout.write(self.style.SUCCESS('✅ Cache preloading completed successfully'))
            else:
                self.stdout.write(self.style.WARNING('⚠️  Cache preloading completed with warnings'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error preloading cache: {e}'))

    def setup_monitoring(self):
        """Setup Redis monitoring."""
        self.stdout.write("Setting up Redis monitoring...")
        
        if setup_redis_monitoring():
            self.stdout.write(self.style.SUCCESS('✅ Redis monitoring setup completed'))
        else:
            self.stdout.write(self.style.ERROR('❌ Error setting up Redis monitoring'))
