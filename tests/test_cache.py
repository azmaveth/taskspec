"""
Tests for the cache modules.
"""

import os
import time
import pytest
import tempfile
import shutil
from pathlib import Path

from taskspec.cache.memory_cache import MemoryCache
from taskspec.cache.disk_cache import DiskCache
from taskspec.cache import get_cache_manager

class TestMemoryCache:
    """Tests for the MemoryCache class."""
    
    def test_set_get(self):
        """Test basic set and get operations."""
        cache = MemoryCache(ttl=3600)
        
        # Set a value
        cache.set("test_key", "test_value")
        
        # Get the value
        assert cache.get("test_key") == "test_value"
        
        # Get a non-existent key
        assert cache.get("non_existent_key") is None
    
    def test_set_delete(self):
        """Test key deletion."""
        cache = MemoryCache(ttl=3600)
        
        # Set a value
        cache.set("test_key", "test_value")
        
        # Check value exists
        assert cache.get("test_key") == "test_value"
        
        # Delete the key
        assert cache.delete("test_key") is True
        
        # Value should be gone
        assert cache.get("test_key") is None
        
        # Deleting non-existent key should return False
        assert cache.delete("non_existent_key") is False
    
    def test_ttl_expiration(self):
        """Test TTL expiration."""
        cache = MemoryCache(ttl=1)  # 1 second TTL
        
        # Set a value
        cache.set("test_key", "test_value")
        
        # Value should be available immediately
        assert cache.get("test_key") == "test_value"
        
        # Wait for TTL to expire
        time.sleep(1.1)
        
        # Value should be expired
        assert cache.get("test_key") is None
    
    def test_clear(self):
        """Test cache clearing."""
        cache = MemoryCache(ttl=3600)
        
        # Set multiple values
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        # Check values exist
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        
        # Clear the cache
        cache.clear()
        
        # Values should be gone
        assert cache.get("key1") is None
        assert cache.get("key2") is None
    
    def test_stats(self):
        """Test cache statistics."""
        cache = MemoryCache(ttl=3600)
        
        # Initial stats
        stats = cache.get_stats()
        assert stats["entries"] == 0
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        
        # Set a value
        cache.set("test_key", "test_value")
        
        # Check entries count
        stats = cache.get_stats()
        assert stats["entries"] == 1
        
        # Get existing key (hit)
        cache.get("test_key")
        stats = cache.get_stats()
        assert stats["hits"] == 1
        
        # Get non-existent key (miss)
        cache.get("non_existent")
        stats = cache.get_stats()
        assert stats["misses"] == 1


class TestDiskCache:
    """Tests for the DiskCache class."""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """Create a temporary directory for disk cache testing."""
        tmp_dir = tempfile.mkdtemp()
        # Create a path to a DB file, not just the directory
        db_path = os.path.join(tmp_dir, "test_cache.db")
        yield db_path
        shutil.rmtree(tmp_dir)
    
    def test_set_get(self, temp_cache_dir):
        """Test basic set and get operations."""
        cache = DiskCache(cache_path=temp_cache_dir, ttl=3600)
        
        # Set a value
        cache.set("test_key", "test_value")
        
        # Get the value
        assert cache.get("test_key") == "test_value"
        
        # Get a non-existent key
        assert cache.get("non_existent_key") is None
        
        # Verify file was created
        assert os.path.exists(temp_cache_dir)
    
    def test_delete(self, temp_cache_dir):
        """Test key deletion."""
        cache = DiskCache(cache_path=temp_cache_dir, ttl=3600)
        
        # Set a value
        cache.set("test_key", "test_value")
        
        # Check value exists
        assert cache.get("test_key") == "test_value"
        
        # Delete the key
        assert cache.delete("test_key") is True
        
        # Value should be gone
        assert cache.get("test_key") is None
    
    def test_ttl_expiration(self, temp_cache_dir):
        """Test TTL expiration."""
        cache = DiskCache(cache_path=temp_cache_dir, ttl=1)  # 1 second TTL
        
        # Set a value
        cache.set("test_key", "test_value")
        
        # Value should be available immediately
        assert cache.get("test_key") == "test_value"
        
        # Wait for TTL to expire
        time.sleep(1.1)
        
        # Value should be expired
        assert cache.get("test_key") is None
    
    def test_clear(self, temp_cache_dir):
        """Test cache clearing."""
        cache = DiskCache(cache_path=temp_cache_dir, ttl=3600)
        
        # Set multiple values
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        # Check values exist
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        
        # Clear the cache
        cache.clear()
        
        # Values should be gone
        assert cache.get("key1") is None
        assert cache.get("key2") is None
    
    def test_stats(self, temp_cache_dir):
        """Test cache statistics."""
        cache = DiskCache(cache_path=temp_cache_dir, ttl=3600)
        
        # Initial stats
        stats = cache.get_stats()
        assert stats["entries"] == 0
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        
        # Set a value
        cache.set("test_key", "test_value")
        
        # Check entries count
        stats = cache.get_stats()
        assert stats["entries"] == 1
        
        # Get existing key (hit)
        cache.get("test_key")
        stats = cache.get_stats()
        assert stats["hits"] == 1
        
        # Get non-existent key (miss)
        cache.get("non_existent")
        stats = cache.get_stats()
        assert stats["misses"] == 1
    
    def test_prune_expired(self, temp_cache_dir):
        """Test pruning expired entries."""
        cache = DiskCache(cache_path=temp_cache_dir, ttl=1)  # 1 second TTL
        
        # Set multiple values
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        # Check values exist
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        
        # Wait for TTL to expire
        time.sleep(1.1)
        
        # Prune expired entries
        pruned = cache.prune_expired()
        assert pruned == 2
        
        # Values should be gone
        assert cache.get("key1") is None
        assert cache.get("key2") is None


def test_get_cache_manager():
    """Test the get_cache_manager factory function."""
    # Test memory cache
    memory_cache = get_cache_manager(cache_type="memory", ttl=3600)
    assert isinstance(memory_cache, MemoryCache)
    
    # Test invalid cache type
    with pytest.raises(ValueError):
        get_cache_manager(cache_type="invalid", ttl=3600)