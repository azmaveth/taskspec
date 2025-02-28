"""
Tests for disk_cache.py error handling.
"""

import os
import pytest
import tempfile
import sqlite3
from unittest.mock import patch, MagicMock

from taskspec.cache.disk_cache import DiskCache

@pytest.fixture
def corrupted_db_path():
    """Create a temporary corrupted database file."""
    tmp_dir = tempfile.mkdtemp()
    db_path = os.path.join(tmp_dir, "corrupted.db")
    
    # Create a file with invalid SQLite data
    with open(db_path, 'wb') as f:
        f.write(b'Not a valid SQLite database')
    
    yield db_path
    
    # Cleanup
    try:
        os.remove(db_path)
        os.rmdir(tmp_dir)
    except:
        pass

def test_disk_cache_error_handling():
    """Test error handling in DiskCache methods with mock SQLite errors."""
    # Create a temporary database path
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = os.path.join(tmp_dir, "test_cache.db")
        
        # Create a cache instance
        cache = DiskCache(cache_path=db_path, ttl=3600)
        
        # Test set method with database error
        with patch('sqlite3.connect', side_effect=sqlite3.Error("Mock DB Error")):
            assert cache.set("test_key", "test_value") is False
        
        # Test delete method with database error
        with patch('sqlite3.connect', side_effect=sqlite3.Error("Mock DB Error")):
            assert cache.delete("test_key") is False
        
        # Test clear method with database error
        with patch('sqlite3.connect', side_effect=sqlite3.Error("Mock DB Error")):
            assert cache.clear() is False
            
        # Test get method with database error
        with patch('sqlite3.connect', side_effect=sqlite3.Error("Mock DB Error")):
            assert cache.get("test_key") is None

def test_disk_cache_prune_expired_empty():
    """Test prune_expired on an empty cache."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = os.path.join(tmp_dir, "test_cache.db")
        cache = DiskCache(cache_path=db_path, ttl=3600)
        
        # Prune with no entries
        assert cache.prune_expired() == 0
        
        # Test prune with database error
        with patch('sqlite3.connect', side_effect=sqlite3.Error("Mock DB Error")):
            assert cache.prune_expired() == 0