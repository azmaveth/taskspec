"""
Disk-based cache implementation for taskspec.
"""

import os
import pickle
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from .base import CacheInterface

class DiskCache(CacheInterface):
    """Disk-based cache implementation using SQLite."""
    
    def __init__(self, cache_path: Optional[str] = None, ttl: int = 86400):
        """
        Initialize disk-based cache.
        
        Args:
            cache_path: Path to cache directory/file (default: ~/.taskspec/cache.db)
            ttl: Time-to-live for cache entries in seconds (default: 24 hours)
        """
        super().__init__(ttl)
        
        # Set default cache path if not provided
        if cache_path is None:
            cache_dir = os.path.join(str(Path.home()), ".taskspec")
            os.makedirs(cache_dir, exist_ok=True)
            cache_path = os.path.join(cache_dir, "cache.db")
        
        self.db_path = cache_path
        self._init_db()
    
    def _init_db(self):
        """Initialize the SQLite database and create tables if they don't exist."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create cache table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value BLOB,
                    timestamp REAL
                )
            ''')
            
            conn.commit()
            conn.close()
        except Exception:
            # Initialization can fail, but we'll continue and handle errors in methods
            pass
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            The cached value or None if not found or expired
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT value, timestamp FROM cache WHERE key = ?", (key,))
            row = cursor.fetchone()
            
            conn.close()
            
            # If key not found
            if not row:
                self.stats["misses"] += 1
                return None
            
            value_blob, timestamp = row
            
            # Check if entry has expired
            if not self.is_fresh(timestamp):
                # Remove expired entry
                self.delete(key)
                self.stats["misses"] += 1
                return None
            
            # Deserialize the value
            value = pickle.loads(value_blob)
            
            self.stats["hits"] += 1
            return value
        except Exception:
            self.stats["misses"] += 1
            return None
    
    def set(self, key: str, value: Any) -> bool:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            
        Returns:
            bool: Success status
        """
        try:
            # Serialize the value
            value_blob = pickle.dumps(value)
            timestamp = time.time()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT OR REPLACE INTO cache VALUES (?, ?, ?)",
                (key, value_blob, timestamp)
            )
            
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if deleted, False if not found or error
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM cache WHERE key = ?", (key,))
            rows_affected = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            return rows_affected > 0
        except Exception:
            return False
    
    def clear(self) -> bool:
        """
        Clear all entries from the cache.
        
        Returns:
            bool: Success status
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM cache")
            
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.
        
        Returns:
            Dict with cache statistics including:
            - hits: Number of cache hits
            - misses: Number of cache misses
            - entries: Number of entries in cache
        """
        stats = self.stats.copy()
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM cache")
            count = cursor.fetchone()[0]
            
            conn.close()
            
            stats["entries"] = count
        except Exception:
            stats["entries"] = 0
        
        return stats
    
    def prune_expired(self) -> int:
        """
        Remove all expired entries from the cache.
        
        Returns:
            int: Number of entries pruned
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Find current time
            current_time = time.time()
            expiration_time = current_time - self.ttl
            
            # Only remove entries if TTL is > 0
            if self.ttl > 0:
                cursor.execute("DELETE FROM cache WHERE timestamp < ?", (expiration_time,))
                pruned = cursor.rowcount
            else:
                pruned = 0
            
            conn.commit()
            conn.close()
            
            return pruned
        except Exception:
            return 0