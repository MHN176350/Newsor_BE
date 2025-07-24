"""
Redis cache configuration and management utilities.
"""
import logging
from django.core.cache import caches

logger = logging.getLogger(__name__)


class RedisManager:
    """Manager for Redis connections and operations."""
    
    def __init__(self):
        self.default_cache = caches['default']
        self.write_back_cache = caches['write_back']
        
    def get_redis_client(self, cache_alias='default'):
        """Get raw Redis client for advanced operations."""
        try:
            cache = caches[cache_alias]
            return cache._cache.get_client(write=False)
        except Exception as e:
            logger.error(f"Error getting Redis client for {cache_alias}: {e}")
            return None
    
    def test_connection(self):
        """Test Redis connections."""
        results = {}
        
        # Test default cache
        try:
            self.default_cache.set('test_key', 'test_value', 60)
            value = self.default_cache.get('test_key')
            results['default'] = value == 'test_value'
            self.default_cache.delete('test_key')
        except Exception as e:
            logger.error(f"Default cache test failed: {e}")
            results['default'] = False
        
        # Test write-back cache
        try:
            self.write_back_cache.set('test_key', 'test_value', 60)
            value = self.write_back_cache.get('test_key')
            results['write_back'] = value == 'test_value'
            self.write_back_cache.delete('test_key')
        except Exception as e:
            logger.error(f"Write-back cache test failed: {e}")
            results['write_back'] = False
        
        return results
    
    def get_cache_info(self):
        """Get cache information and statistics."""
        info = {}
        
        try:
            redis_client = self.get_redis_client('default')
            if redis_client:
                redis_info = redis_client.info()
                info['redis_version'] = redis_info.get('redis_version')
                info['used_memory'] = redis_info.get('used_memory_human')
                info['connected_clients'] = redis_info.get('connected_clients')
                info['total_commands_processed'] = redis_info.get('total_commands_processed')
                info['keyspace_hits'] = redis_info.get('keyspace_hits')
                info['keyspace_misses'] = redis_info.get('keyspace_misses')
                
                # Calculate hit ratio
                hits = info.get('keyspace_hits', 0)
                misses = info.get('keyspace_misses', 0)
                total = hits + misses
                info['hit_ratio'] = (hits / total * 100) if total > 0 else 0
        except Exception as e:
            logger.error(f"Error getting cache info: {e}")
        
        return info
    
    def clear_all_caches(self):
        """Clear all application caches."""
        try:
            self.default_cache.clear()
            self.write_back_cache.clear()
            logger.info("All caches cleared")
            return True
        except Exception as e:
            logger.error(f"Error clearing caches: {e}")
            return False
    
    def get_key_pattern(self, pattern, cache_alias='default'):
        """Get keys matching a pattern."""
        try:
            redis_client = self.get_redis_client(cache_alias)
            if redis_client:
                cache = caches[cache_alias]
                full_pattern = f"{cache.key_prefix}*{pattern}*"
                keys = redis_client.keys(full_pattern)
                return [key.decode().replace(f"{cache.key_prefix}:", "") for key in keys]
            return []
        except Exception as e:
            logger.error(f"Error getting keys with pattern {pattern}: {e}")
            return []
    
    def delete_pattern(self, pattern, cache_alias='default'):
        """Delete keys matching a pattern."""
        try:
            keys = self.get_key_pattern(pattern, cache_alias)
            if keys:
                cache = caches[cache_alias]
                cache.delete_many(keys)
                logger.info(f"Deleted {len(keys)} keys matching pattern: {pattern}")
                return len(keys)
            return 0
        except Exception as e:
            logger.error(f"Error deleting keys with pattern {pattern}: {e}")
            return 0


def ensure_redis_connection():
    """Ensure Redis is connected and working."""
    manager = RedisManager()
    results = manager.test_connection()
    
    if not all(results.values()):
        logger.error(f"Redis connection test failed: {results}")
        return False
    
    logger.info("Redis connections tested successfully")
    return True


def setup_redis_monitoring():
    """Setup Redis monitoring and logging."""
    try:
        manager = RedisManager()
        info = manager.get_cache_info()
        
        logger.info(f"Redis setup - Version: {info.get('redis_version', 'unknown')}")
        logger.info(f"Memory usage: {info.get('used_memory', 'unknown')}")
        logger.info(f"Hit ratio: {info.get('hit_ratio', 0):.2f}%")
        
        return True
    except Exception as e:
        logger.error(f"Error setting up Redis monitoring: {e}")
        return False


# Global Redis manager instance
redis_manager = RedisManager()
