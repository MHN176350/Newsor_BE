"""
Base cache interface and implementations.
"""
from abc import ABC, abstractmethod
from typing import Any, Optional, List, Dict
import logging
from datetime import datetime
from django.core.cache import caches
from django.conf import settings

logger = logging.getLogger(__name__)


class CacheInterface(ABC):
    """Abstract base class for cache implementations."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> bool:
        """Set value in cache."""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        """Clear all cache."""
        pass


class RedisCache(CacheInterface):
    """Redis cache implementation."""
    
    def __init__(self, cache_alias: str = 'default'):
        self.cache = caches[cache_alias]
        self.cache_alias = cache_alias
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache."""
        try:
            return self.cache.get(key)
        except Exception as e:
            logger.error(f"Error getting key {key} from cache: {e}")
            return None
    
    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> bool:
        """Set value in Redis cache."""
        try:
            if timeout is None:
                timeout = getattr(settings, 'CACHE_TIMEOUT', 300)
            return self.cache.set(key, value, timeout)
        except Exception as e:
            logger.error(f"Error setting key {key} in cache: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from Redis cache."""
        try:
            return self.cache.delete(key) > 0
        except Exception as e:
            logger.error(f"Error deleting key {key} from cache: {e}")
            return False
    
    def clear(self) -> bool:
        """Clear all cache."""
        try:
            self.cache.clear()
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
    
    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from cache."""
        try:
            return self.cache.get_many(keys)
        except Exception as e:
            logger.error(f"Error getting multiple keys from cache: {e}")
            return {}
    
    def set_many(self, data: Dict[str, Any], timeout: Optional[int] = None) -> bool:
        """Set multiple values in cache."""
        try:
            if timeout is None:
                timeout = getattr(settings, 'CACHE_TIMEOUT', 300)
            self.cache.set_many(data, timeout)
            return True
        except Exception as e:
            logger.error(f"Error setting multiple keys in cache: {e}")
            return False
    
    def delete_many(self, keys: List[str]) -> bool:
        """Delete multiple values from cache."""
        try:
            self.cache.delete_many(keys)
            return True
        except Exception as e:
            logger.error(f"Error deleting multiple keys from cache: {e}")
            return False
    
    def has_key(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            return self.cache.has_key(key)
        except Exception as e:
            logger.error(f"Error checking key {key} in cache: {e}")
            return False
    
    def incr(self, key: str, delta: int = 1) -> Optional[int]:
        """Increment a value in cache."""
        try:
            return self.cache.incr(key, delta)
        except Exception as e:
            logger.error(f"Error incrementing key {key} in cache: {e}")
            return None
    
    def decr(self, key: str, delta: int = 1) -> Optional[int]:
        """Decrement a value in cache."""
        try:
            return self.cache.decr(key, delta)
        except Exception as e:
            logger.error(f"Error decrementing key {key} in cache: {e}")
            return None


class WriteBackCache:
    """
    Write-back cache implementation using Redis.
    
    This cache stores write operations in Redis and periodically flushes them
    to the database in batches for improved performance.
    """
    
    def __init__(self, cache_alias: str = 'write_back'):
        self.cache = caches[cache_alias]
        self.cache_alias = cache_alias
        self.batch_size = getattr(settings, 'WRITE_BACK_BATCH_SIZE', 100)
        self.flush_interval = getattr(settings, 'WRITE_BACK_FLUSH_INTERVAL', 60)
    
    def queue_write(self, operation_type: str, model_name: str, object_id: str, data: Dict[str, Any]) -> bool:
        """Queue a write operation for later execution."""
        try:
            operation = {
                'type': operation_type,  # 'create', 'update', 'delete'
                'model': model_name,
                'id': object_id,
                'data': data,
                'timestamp': datetime.now().isoformat(),
            }
            
            key = f"write_operation:{model_name}:{object_id}:{operation_type}"
            return self.cache.set(key, operation)
        except Exception as e:
            logger.error(f"Error queuing write operation: {e}")
            return False
    
    def get_pending_operations(self, model_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all pending write operations."""
        try:
            # This is a simplified implementation for testing
            # In a real scenario, you'd use Redis SCAN or maintain a list of pending operations
            
            # For now, we'll return an empty list as this is mainly for demonstration
            # You could implement this by maintaining a Redis set of operation keys
            logger.info("Getting pending operations (simplified implementation)")
            return []
            
        except Exception as e:
            logger.error(f"Error getting pending operations: {e}")
            return []
    
    def flush_operations(self, model_name: Optional[str] = None) -> int:
        """Flush pending operations to the database."""
        operations = self.get_pending_operations(model_name)
        if not operations:
            return 0
        
        flushed_count = 0
        batch = []
        
        for operation in operations:
            batch.append(operation)
            
            if len(batch) >= self.batch_size:
                if self._execute_batch(batch):
                    self._remove_operations(batch)
                    flushed_count += len(batch)
                batch = []
        
        # Process remaining operations
        if batch:
            if self._execute_batch(batch):
                self._remove_operations(batch)
                flushed_count += len(batch)
        
        logger.info(f"Flushed {flushed_count} write operations to database")
        return flushed_count
    
    def _execute_batch(self, operations: List[Dict[str, Any]]) -> bool:
        """Execute a batch of operations."""
        try:
            # Group operations by model and type for efficient processing
            from django.apps import apps
            
            for operation in operations:
                model_name = operation['model']
                operation_type = operation['type']
                object_id = operation['id']
                data = operation['data']
                
                try:
                    model_class = apps.get_model('api', model_name)
                    
                    if operation_type == 'create':
                        model_class.objects.create(**data)
                    elif operation_type == 'update':
                        model_class.objects.filter(id=object_id).update(**data)
                    elif operation_type == 'delete':
                        model_class.objects.filter(id=object_id).delete()
                        
                except Exception as e:
                    logger.error(f"Error executing operation {operation}: {e}")
                    continue
            
            return True
        except Exception as e:
            logger.error(f"Error executing batch: {e}")
            return False
    
    def _remove_operations(self, operations: List[Dict[str, Any]]) -> None:
        """Remove completed operations from cache."""
        keys_to_delete = []
        for operation in operations:
            key = f"write_operation:{operation['model']}:{operation['id']}:{operation['type']}"
            keys_to_delete.append(key)
        
        if keys_to_delete:
            self.cache.delete_many(keys_to_delete)
    
    def clear_pending_operations(self, model_name: Optional[str] = None) -> bool:
        """Clear all pending operations."""
        try:
            operations = self.get_pending_operations(model_name)
            if operations:
                self._remove_operations(operations)
            return True
        except Exception as e:
            logger.error(f"Error clearing pending operations: {e}")
            return False


# Global cache instances
default_cache = RedisCache('default')
write_back_cache = WriteBackCache('write_back')
