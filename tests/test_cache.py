"""
Tests for the cache modules.
"""

import os
import time
import pytest
import tempfile
import shutil
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock

from taskspec.cache.memory_cache import MemoryCache
from taskspec.cache.disk_cache import DiskCache
from taskspec.cache.base import CacheInterface
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
        
    def test_set_get_complex_data(self):
        """Test storing and retrieving complex data structures."""
        cache = MemoryCache(ttl=3600)
        
        # Test with dict
        complex_dict = {"a": 1, "b": [1, 2, 3], "c": {"nested": True}}
        cache.set("dict_key", complex_dict)
        assert cache.get("dict_key") == complex_dict
        
        # Test with list
        complex_list = [1, "string", {"a": 1}, [1, 2, 3]]
        cache.set("list_key", complex_list)
        assert cache.get("list_key") == complex_list
        
        # Test with custom object
        class TestObject:
            def __init__(self, value):
                self.value = value
                
        test_obj = TestObject("test")
        cache.set("obj_key", test_obj)
        retrieved = cache.get("obj_key")
        assert retrieved is not None
        assert retrieved.value == "test"
    
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
        
    def test_zero_ttl(self):
        """Test with TTL=0 (indefinite storage)."""
        cache = MemoryCache(ttl=0)  # Indefinite TTL
        
        # Set a value
        cache.set("test_key", "test_value")
        
        # Value should be available
        assert cache.get("test_key") == "test_value"
        
        # Sleep to ensure the cache isn't using a different time mechanism
        time.sleep(0.1)
        
        # Value should still be available
        assert cache.get("test_key") == "test_value"
        
    def test_negative_ttl(self):
        """Test with negative TTL (should be treated as 0)."""
        cache = MemoryCache(ttl=-10)  # Negative TTL
        
        # Set a value
        cache.set("test_key", "test_value")
        
        # Value should be available
        assert cache.get("test_key") == "test_value"
        
        # Sleep to ensure the cache isn't using a different time mechanism
        time.sleep(0.1)
        
        # Value should still be available
        assert cache.get("test_key") == "test_value"
    
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


def test_base_cache_generate_key():
    """Test the generate_key method in the base CacheInterface class."""
    # Create a concrete implementation of the abstract class for testing
    class TestCache(CacheInterface):
        def get(self, key): pass
        def set(self, key, value): pass
        def delete(self, key): pass
        def clear(self): pass
        def get_stats(self): pass
    
    cache = TestCache(ttl=3600)
    
    # Test key generation with simple values
    key1 = cache.generate_key("test prompt", "model1", 0.5)
    assert isinstance(key1, str)
    
    # Test key generation with complex values
    complex_prompt = {"messages": [{"role": "user", "content": "Hello"}]}
    key2 = cache.generate_key(str(complex_prompt), "model2", 0.7)
    assert isinstance(key2, str)
    
    # Test deterministic behavior (same inputs = same key)
    key3 = cache.generate_key("test prompt", "model1", 0.5)
    assert key1 == key3
    
    # Test different inputs produce different keys
    key4 = cache.generate_key("different prompt", "model1", 0.5)
    assert key1 != key4
    
    # Verify implementation matches expected behavior
    expected_key = hashlib.md5("test prompt|model1|0.5".encode()).hexdigest()
    assert key1 == expected_key

def test_get_cache_manager():
    """Test the get_cache_manager factory function."""
    # Test memory cache
    memory_cache = get_cache_manager(cache_type="memory", ttl=3600)
    assert isinstance(memory_cache, MemoryCache)
    
    # Test disk cache
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = os.path.join(tmp_dir, "test_cache.db")
        disk_cache = get_cache_manager(cache_type="disk", cache_path=db_path, ttl=3600)
        assert isinstance(disk_cache, DiskCache)
    
    # Test invalid cache type
    with pytest.raises(ValueError):
        get_cache_manager(cache_type="invalid", ttl=3600)
        
    # Test missing cache_path for disk cache
    with pytest.raises(ValueError):
        get_cache_manager(cache_type="disk", ttl=3600)