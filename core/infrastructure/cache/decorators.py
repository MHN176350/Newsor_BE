"""
Cache decorators for easy integration with Django views and GraphQL resolvers.
"""
import functools
import logging
from typing import Callable
from django.core.cache import caches
from .managers import news_cache, category_cache

logger = logging.getLogger(__name__)


def cache_result(cache_key: str, timeout: int = 300, cache_alias: str = 'default'):
    """
    Decorator to cache function results.
    
    Args:
        cache_key: Key to store the result in cache
        timeout: Cache timeout in seconds
        cache_alias: Which cache backend to use
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache = caches[cache_alias]
            
            # Try to get from cache first
            result = cache.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return result
            
            # Execute function and cache result
            logger.debug(f"Cache miss for key: {cache_key}")
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            
            return result
        return wrapper
    return decorator


def cache_with_key_generator(key_generator: Callable, timeout: int = 300, cache_alias: str = 'default'):
    """
    Decorator to cache function results with dynamic key generation.
    
    Args:
        key_generator: Function to generate cache key from function arguments
        timeout: Cache timeout in seconds
        cache_alias: Which cache backend to use
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache = caches[cache_alias]
            
            # Generate cache key
            cache_key = key_generator(*args, **kwargs)
            
            # Try to get from cache first
            result = cache.get(cache_key)
            if result is not None:
                logger.debug(f"Cache for key: {cache_key}")
                return result
            
            # Execute function and cache result
            logger.debug(f"Cache miss for key: {cache_key}")
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            
            return result
        return wrapper
    return decorator


def invalidate_cache_on_change(cache_keys: list, models: list = None):
    """
    Decorator to invalidate cache when certain models are modified.
    
    Args:
        cache_keys: List of cache keys to invalidate
        models: List of model names that trigger invalidation
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            # Invalidate specified cache keys
            cache = caches['default']
            for key in cache_keys:
                cache.delete(key)
                logger.debug(f"Invalidated cache key: {key}")
            
            return result
        return wrapper
    return decorator


# Specific decorators for Newsor models

def cache_news_article(timeout: int = 3600):
    """Cache news article by ID or slug."""
    def key_generator(*args, **kwargs):
        # Extract article ID or slug from arguments
        if args and hasattr(args[0], 'id'):
            return f"article:id:{args[0].id}"
        elif 'id' in kwargs:
            return f"article:id:{kwargs['id']}"
        elif 'slug' in kwargs:
            return f"article:slug:{kwargs['slug']}"
        else:
            return "article:unknown"
    
    return cache_with_key_generator(key_generator, timeout)


def cache_user_data(timeout: int = 1800):
    """Cache user data by ID or username."""
    def key_generator(*args, **kwargs):
        if args and hasattr(args[0], 'id'):
            return f"user:id:{args[0].id}"
        elif 'user_id' in kwargs:
            return f"user:id:{kwargs['user_id']}"
        elif 'username' in kwargs:
            return f"user:username:{kwargs['username']}"
        else:
            return "user:unknown"
    
    return cache_with_key_generator(key_generator, timeout)


def cache_category_data(timeout: int = 3600):
    """Cache category data."""
    def key_generator(*args, **kwargs):
        if 'category_id' in kwargs:
            return f"category:id:{kwargs['category_id']}"
        elif 'slug' in kwargs:
            return f"category:slug:{kwargs['slug']}"
        else:
            return "categories:all"
    
    return cache_with_key_generator(key_generator, timeout)


def cache_comments(timeout: int = 1800):
    """Cache comments for articles."""
    def key_generator(*args, **kwargs):
        article_id = kwargs.get('article_id', 'unknown')
        page = kwargs.get('page', 1)
        per_page = kwargs.get('per_page', 20)
        return f"comments:article:{article_id}:page:{page}:per_page:{per_page}"
    
    return cache_with_key_generator(key_generator, timeout)


# Write-back decorators

def write_back_on_change(model_name: str, operation_type: str = 'update'):
    """
    Decorator to queue write operations for write-back strategy.
    
    Args:
        model_name: Name of the model being modified
        operation_type: Type of operation ('create', 'update', 'delete')
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            # Extract object ID and data for write-back
            try:
                if hasattr(result, 'id'):
                    object_id = str(result.id)
                    data = {}
                    
                    # Queue for write-back
                    from .base import write_back_cache
                    write_back_cache.queue_write(operation_type, model_name, object_id, data)
                    logger.debug(f"Queued {operation_type} operation for {model_name}:{object_id}")
            except Exception as e:
                logger.error(f"Error queuing write-back operation: {e}")
            
            return result
        return wrapper
    return decorator


# Cache warming decorators

def warm_cache_on_startup():
    """Decorator to warm cache when application starts."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Warm up essential caches
            try:
                # Warm categories cache
                logger.info("Warming up categories cache...")
                # This would call the actual function to populate cache
                
                # Warm trending articles cache
                logger.info("Warming up trending articles cache...")
                
                # Warm popular users cache
                logger.info("Warming up users cache...")
                
            except Exception as e:
                logger.error(f"Error warming cache: {e}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Utility functions for cache management

def clear_all_caches():
    """Clear all application caches."""
    try:
        default_cache = caches['default']
        write_back_cache = caches['write_back']
        
        default_cache.clear()
        write_back_cache.clear()
        
        logger.info("All caches cleared successfully")
        return True
    except Exception as e:
        logger.error(f"Error clearing caches: {e}")
        return False


def get_cache_stats():
    """Get cache statistics."""
    try:
        stats = {
            'default_cache': {},
            'write_back_cache': {},
        }
        
        # This would require implementing cache statistics
        # Redis INFO command could be used here
        
        return stats
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return {}


def preload_essential_data():
    """Preload essential data into cache."""
    try:
        logger.info("Preloading essential data into cache...")
        
        # Preload categories
        from api.models import Category
        categories = list(Category.objects.filter(is_active=True).values())
        category_cache.cache_all_categories(categories)
        
        # Preload trending articles
        from api.models import News
        trending = list(News.objects.filter(
            status='published'
        ).order_by('-view_count')[:10].values())
        news_cache.cache_trending_articles(trending)
        
        logger.info("Essential data preloaded successfully")
        return True
    except Exception as e:
        logger.error(f"Error preloading data: {e}")
        return False
