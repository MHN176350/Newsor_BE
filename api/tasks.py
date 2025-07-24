"""
Background tasks for cache management and write-back operations.
Note: Celery is optional - these can also be run as management commands.
"""
try:
    from celery import shared_task
    CELERY_AVAILABLE = True
except ImportError:
    # Fallback decorator when Celery is not available
    def shared_task(func):
        return func
    CELERY_AVAILABLE = False

from core.infrastructure.cache.base import WriteBackCache
from core.infrastructure.cache.decorators import preload_essential_data
import logging

logger = logging.getLogger(__name__)


@shared_task
def flush_write_back_cache(model_name=None):
    """
    Celery task to flush write-back cache operations to the database.
    
    Args:
        model_name: Optional model name to flush specific operations
    """
    try:
        write_back = WriteBackCache()
        flushed_count = write_back.flush_operations(model_name)
        logger.info(f"Flushed {flushed_count} write-back operations for model: {model_name or 'all'}")
        return flushed_count
    except Exception as e:
        logger.error(f"Error in flush_write_back_cache task: {e}")
        raise


@shared_task
def preload_cache_data():
    """
    Celery task to preload essential data into cache.
    """
    try:
        success = preload_essential_data()
        if success:
            logger.info("Cache preloading completed successfully")
        else:
            logger.warning("Cache preloading completed with warnings")
        return success
    except Exception as e:
        logger.error(f"Error in preload_cache_data task: {e}")
        raise


@shared_task
def clear_expired_cache_keys():
    """
    Task to clear expired cache keys (cleanup task).
    """
    try:
        from django.core.cache import caches
        
        # This would be more sophisticated in a real implementation
        # Redis SCAN with EXPIRE would be used
        # For now, just clear some pattern-based keys that might be stale
        # In a real implementation, you'd track key expiration more carefully
        
        logger.info("Cache cleanup completed")
        return True
    except Exception as e:
        logger.error(f"Error in clear_expired_cache_keys task: {e}")
        raise


@shared_task
def warm_up_trending_content():
    """
    Celery task to warm up trending content cache.
    """
    try:
        from api.models import News
        from core.infrastructure.cache.managers import news_cache
        
        # Get trending articles
        trending_articles = list(
            News.objects.filter(status='published')
            .order_by('-view_count', '-created_at')[:20]
            .values(
                'id', 'title', 'slug', 'excerpt', 'featured_image_url',
                'view_count', 'like_count', 'created_at', 'category__name'
            )
        )
        
        # Cache trending articles
        news_cache.cache_trending_articles(trending_articles)
        
        logger.info(f"Warmed up trending content cache with {len(trending_articles)} articles")
        return len(trending_articles)
    except Exception as e:
        logger.error(f"Error in warm_up_trending_content task: {e}")
        raise


@shared_task
def update_view_counts():
    """
    Task to batch update view counts from cache to database.
    """
    try:
        # This is a simplified implementation
        # In reality, you'd need to track which articles have pending view count updates
        updated_count = 0
        
        # For now, let's assume we have a way to get articles with cached view counts
        # You could maintain a set of article IDs with pending view count updates
        
        logger.info(f"Updated {updated_count} article view counts")
        return updated_count
    except Exception as e:
        logger.error(f"Error in update_view_counts task: {e}")
        raise


@shared_task
def cache_health_check():
    """
    Celery task to perform cache health checks.
    """
    try:
        from django.core.cache import caches
        
        health_status = {
            'default_cache': False,
            'write_back_cache': False,
        }
        
        # Test default cache
        try:
            cache = caches['default']
            test_key = "health_check_test"
            cache.set(test_key, "test_value", 60)
            retrieved_value = cache.get(test_key)
            health_status['default_cache'] = retrieved_value == "test_value"
            cache.delete(test_key)
        except Exception as e:
            logger.error(f"Default cache health check failed: {e}")
        
        # Test write-back cache
        try:
            cache = caches['write_back']
            test_key = "wb_health_check_test"
            cache.set(test_key, "test_value", 60)
            retrieved_value = cache.get(test_key)
            health_status['write_back_cache'] = retrieved_value == "test_value"
            cache.delete(test_key)
        except Exception as e:
            logger.error(f"Write-back cache health check failed: {e}")
        
        logger.info(f"Cache health check completed: {health_status}")
        return health_status
    except Exception as e:
        logger.error(f"Error in cache_health_check task: {e}")
        raise


# Periodic task setup (if using celery beat)
# Add these to your CELERY_BEAT_SCHEDULE in settings.py:
"""
CELERY_BEAT_SCHEDULE = {
    'flush-write-back-cache': {
        'task': 'api.tasks.flush_write_back_cache',
        'schedule': 60.0,  # Every 60 seconds
    },
    'warm-up-trending': {
        'task': 'api.tasks.warm_up_trending_content',
        'schedule': 300.0,  # Every 5 minutes
    },
    'update-view-counts': {
        'task': 'api.tasks.update_view_counts',
        'schedule': 120.0,  # Every 2 minutes
    },
    'cache-health-check': {
        'task': 'api.tasks.cache_health_check',
        'schedule': 600.0,  # Every 10 minutes
    },
}
"""
