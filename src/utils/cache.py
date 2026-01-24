"""Caching utilities for performance optimization."""

import json
import hashlib
from typing import Optional, Any, Dict, Union
import redis
from loguru import logger
from src.core.config import settings


class CacheManager:
    """Centralized caching management with Redis backend."""
    
    def __init__(self):
        """Initialize cache manager with Redis connection."""
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            self.enabled = True
            logger.info("Redis cache initialized successfully")
        except Exception as e:
            logger.warning(f"Redis cache initialization failed: {e}. Falling back to in-memory cache.")
            self.redis_client = None
            self.enabled = False
            self._memory_cache = {}
    
    def _generate_key(self, prefix: str, identifier: str) -> str:
        """Generate cache key with prefix and hashed identifier."""
        hash_object = hashlib.md5(identifier.encode())
        return f"{prefix}:{hash_object.hexdigest()}"
    
    def get(self, key: str, prefix: str = "cache") -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key or identifier
            prefix: Cache key prefix
            
        Returns:
            Cached value or None if not found/expired
        """
        cache_key = self._generate_key(prefix, key)
        
        try:
            if self.enabled and self.redis_client:
                # Try Redis cache
                cached_value = self.redis_client.get(cache_key)
                if cached_value:
                    try:
                        return json.loads(cached_value)
                    except json.JSONDecodeError:
                        # Invalid JSON, remove corrupted entry
                        self.redis_client.delete(cache_key)
                        return None
            else:
                # Try memory cache
                return self._memory_cache.get(cache_key)
                
        except Exception as e:
            logger.error(f"Cache get error for key {cache_key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600, prefix: str = "cache") -> bool:
        """Set value in cache with TTL.
        
        Args:
            key: Cache key or identifier
            value: Value to cache
            ttl: Time to live in seconds
            prefix: Cache key prefix
            
        Returns:
            True if successful, False otherwise
        """
        cache_key = self._generate_key(prefix, key)
        
        try:
            serialized_value = json.dumps(value, default=str)
            
            if self.enabled and self.redis_client:
                # Use Redis cache
                result = self.redis_client.setex(cache_key, ttl, serialized_value)
                return result is not None
            else:
                # Use memory cache
                self._memory_cache[cache_key] = {
                    'value': value,
                    'expires': self._get_current_time() + ttl
                }
                return True
                
        except Exception as e:
            logger.error(f"Cache set error for key {cache_key}: {e}")
            return False
    
    def delete(self, key: str, prefix: str = "cache") -> bool:
        """Delete value from cache.
        
        Args:
            key: Cache key or identifier
            prefix: Cache key prefix
            
        Returns:
            True if successful, False otherwise
        """
        cache_key = self._generate_key(prefix, key)
        
        try:
            if self.enabled and self.redis_client:
                result = self.redis_client.delete(cache_key)
                return result > 0
            else:
                if cache_key in self._memory_cache:
                    del self._memory_cache[cache_key]
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Cache delete error for key {cache_key}: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all cache entries matching pattern.
        
        Args:
            pattern: Pattern to match (supports * wildcards)
            
        Returns:
            Number of entries cleared
        """
        try:
            if self.enabled and self.redis_client:
                # Use Redis pattern deletion
                keys = self.redis_client.keys(f"{pattern}*")
                if keys:
                    return self.redis_client.delete(*keys)
                return 0
            else:
                # Clear memory cache entries
                cleared = 0
                pattern_full = self._generate_key(pattern.replace('*', ''), '')
                keys_to_delete = [
                    key for key in self._memory_cache.keys() 
                    if key.startswith(pattern_full.replace('*', ''))
                ]
                for key in keys_to_delete:
                    del self._memory_cache[key]
                    cleared += 1
                return cleared
                
        except Exception as e:
            logger.error(f"Cache clear pattern error: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            if self.enabled and self.redis_client:
                info = self.redis_client.info()
                return {
                    'enabled': True,
                    'backend': 'redis',
                    'connected': True,
                    'used_memory': info.get('used_memory_human', 'N/A'),
                    'connected_clients': info.get('connected_clients', 'N/A'),
                    'total_commands_processed': info.get('total_commands_processed', 'N/A')
                }
            else:
                return {
                    'enabled': True,
                    'backend': 'memory',
                    'connected': False,
                    'entry_count': len(self._memory_cache),
                    'memory_usage': 'N/A'
                }
        except Exception as e:
            return {
                'enabled': False,
                'backend': 'none',
                'error': str(e)
            }
    
    def _get_current_time(self) -> int:
        """Get current timestamp for memory cache expiration."""
        import time
        return int(time.time())
    
    def _cleanup_expired_memory_entries(self):
        """Clean up expired entries in memory cache."""
        if not self.enabled:
            current_time = self._get_current_time()
            expired_keys = [
                key for key, entry in self._memory_cache.items()
                if entry.get('expires', 0) < current_time
            ]
            for key in expired_keys:
                del self._memory_cache[key]


# Global cache manager instance
cache_manager = CacheManager()


class CacheDecorator:
    """Decorator for easy caching of function results."""
    
    @staticmethod
    def cached(ttl: int = 3600, key_prefix: str = "func"):
        """Decorator to cache function results.
        
        Args:
            ttl: Time to live in seconds
            key_prefix: Cache key prefix
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                # Generate cache key from function signature
                func_name = f"{func.__module__}.{func.__name__}"
                args_str = str(args) + str(sorted(kwargs.items()))
                cache_key = f"{key_prefix}:{func_name}:{args_str}"
                
                # Try to get from cache
                cached_result = cache_manager.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for {func_name}")
                    return cached_result
                
                # Execute function and cache result
                try:
                    result = func(*args, **kwargs)
                    cache_manager.set(cache_key, result, ttl)
                    logger.debug(f"Cache miss for {func_name}, result cached")
                    return result
                except Exception as e:
                    logger.error(f"Function execution failed: {e}")
                    raise
                    
            return wrapper
        return decorator