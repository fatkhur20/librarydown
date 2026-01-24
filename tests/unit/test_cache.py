"""Unit tests for caching utilities."""

import pytest
import time
from unittest.mock import Mock, patch
from src.utils.cache import CacheManager, CacheDecorator


class TestCacheManager:
    
    @pytest.fixture
    def cache_manager(self):
        """Create cache manager instance for testing."""
        return CacheManager()
    
    def test_set_and_get(self, cache_manager):
        """Test basic set and get operations."""
        key = "test_key"
        value = {"data": "test_value", "number": 42}
        
        # Set value
        result = cache_manager.set(key, value, ttl=60)
        assert result is True
        
        # Get value
        cached_value = cache_manager.get(key)
        assert cached_value == value
    
    def test_get_nonexistent_key(self, cache_manager):
        """Test getting non-existent key."""
        result = cache_manager.get("nonexistent_key")
        assert result is None
    
    def test_delete_key(self, cache_manager):
        """Test deleting a key."""
        key = "test_delete_key"
        cache_manager.set(key, "test_value", ttl=60)
        
        # Verify key exists
        assert cache_manager.get(key) is not None
        
        # Delete key
        result = cache_manager.delete(key)
        assert result is True
        
        # Verify key is deleted
        assert cache_manager.get(key) is None
    
    def test_ttl_expiration(self, cache_manager):
        """Test TTL expiration (memory cache)."""
        if cache_manager.enabled:
            pytest.skip("Skipping TTL test for Redis cache")
            
        key = "ttl_test_key"
        value = "temporary_value"
        
        # Set with short TTL
        cache_manager.set(key, value, ttl=1)  # 1 second TTL
        
        # Should be available immediately
        assert cache_manager.get(key) == value
        
        # Wait for expiration
        time.sleep(2)
        
        # Should be expired
        assert cache_manager.get(key) is None
    
    def test_clear_pattern(self, cache_manager):
        """Test clearing cache by pattern."""
        # Set multiple keys with same prefix
        cache_manager.set("prefix:item1", "value1", ttl=60)
        cache_manager.set("prefix:item2", "value2", ttl=60)
        cache_manager.set("other:item3", "value3", ttl=60)
        
        # Clear pattern
        cleared_count = cache_manager.clear_pattern("prefix:")
        assert cleared_count >= 2  # At least 2 items cleared
        
        # Verify prefix items are cleared
        assert cache_manager.get("prefix:item1") is None
        assert cache_manager.get("prefix:item2") is None
        
        # Verify other items remain
        assert cache_manager.get("other:item3") is not None
    
    def test_get_stats(self, cache_manager):
        """Test getting cache statistics."""
        stats = cache_manager.get_stats()
        
        assert isinstance(stats, dict)
        assert "enabled" in stats
        
        if stats["enabled"]:
            assert "backend" in stats
            assert stats["backend"] in ["redis", "memory"]


class TestCacheDecorator:
    
    def test_cached_decorator(self):
        """Test cache decorator functionality."""
        call_count = 0
        
        @CacheDecorator.cached(ttl=60, key_prefix="test")
        def expensive_function(x, y):
            nonlocal call_count
            call_count += 1
            return x + y
        
        # First call - should execute function
        result1 = expensive_function(5, 3)
        assert result1 == 8
        assert call_count == 1
        
        # Second call with same args - should use cache
        result2 = expensive_function(5, 3)
        assert result2 == 8
        assert call_count == 1  # Function not called again
        
        # Call with different args - should execute function
        result3 = expensive_function(10, 20)
        assert result3 == 30
        assert call_count == 2  # Function called again


if __name__ == "__main__":
    pytest.main([__file__])