"""
Disk-based SQLite cache implementation for taskspec.
"""

import os
import sqlite3
import time
import json
import pickle
from typing import Any, Dict, Optional, Tuple
from pathlib import Path

from .base import CacheInterface

class DiskCache(CacheInterface):
    """Disk-based SQLite cache implementation."""
    
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
        
        # Create stats table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stats (
                name TEXT PRIMARY KEY,
                value INTEGER
            )
        ''')
        
        # Initialize stats if they don't exist
        for stat in ["hits", "misses"]:
            cursor.execute("INSERT OR IGNORE INTO stats VALUES (?, 0)", (stat,))
        
        conn.commit()
        conn.close()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            The cached value or None if not found or expired
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT value, timestamp FROM cache WHERE key = ?", (key,))
        result = cursor.fetchone()
        
        if result is None:
            # Update miss stats
            cursor.execute("UPDATE stats SET value = value + 1 WHERE name = 'misses'")
            conn.commit()
            conn.close()
            self.stats["misses"] += 1
            return None
        
        value_blob, timestamp = result
        
        if not self.is_fresh(timestamp):
            # Entry has expired, remove it
            cursor.execute("DELETE FROM cache WHERE key = ?", (key,))
            # Update miss stats
            cursor.execute("UPDATE stats SET value = value + 1 WHERE name = 'misses'")
            conn.commit()
            conn.close()
            self.stats["misses"] += 1
            return None
        
        # Update hit stats
        cursor.execute("UPDATE stats SET value = value + 1 WHERE name = 'hits'")
        conn.commit()
        conn.close()
        self.stats["hits"] += 1
        
        # Deserialize the value
        return pickle.loads(value_blob)
    
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
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Serialize the value
            value_blob = pickle.dumps(value)
            timestamp = time.time()
            
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
            bool: True if deleted, False if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM cache WHERE key = ?", (key,))
        rows_affected = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return rows_affected > 0
    
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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get the database stats
        cursor.execute("SELECT name, value FROM stats")
        db_stats = dict(cursor.fetchall())
        
        # Get the number of entries
        cursor.execute("SELECT COUNT(*) FROM cache")
        entries = cursor.fetchone()[0]
        
        conn.close()
        
        # Update in-memory stats from DB
        self.stats["hits"] = db_stats.get("hits", 0)
        self.stats["misses"] = db_stats.get("misses", 0)
        
        # Combine and return stats
        stats = self.stats.copy()
        stats["entries"] = entries
        return stats

    def prune_expired(self) -> int:
        """
        Remove all expired entries from the cache.
        
        Returns:
            int: Number of entries removed
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        expiry_time = time.time() - self.ttl
        cursor.execute("DELETE FROM cache WHERE timestamp < ?", (expiry_time,))
        removed = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return removed
