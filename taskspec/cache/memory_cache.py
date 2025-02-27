"""
In-memory cache implementation for taskspec.
"""

import time
from typing import Any, Dict, Optional, Tuple

from .base import CacheInterface

class MemoryCache(CacheInterface):
    """In-memory cache implementation."""
    
    def __init__(self, ttl: int = 86400):
        """
        Initialize in-memory cache.
        
        Args:
            ttl: Time-to-live for cache entries in seconds (default: 24 hours)
        """
        super().__init__(ttl)
        self._cache = {}  # Dict to store key-value pairs
        self._timestamps = {}  # Dict to store entry timestamps
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            The cached value or None if not found or expired
        """
        if key not in self._cache:
            self.stats["misses"] += 1
            return None
        
        timestamp = self._timestamps.get(key, 0)
        if not self.is_fresh(timestamp):
            # Entry has expired, remove it
            self.delete(key)
            self.stats["misses"] += 1
            return None
        
        self.stats["hits"] += 1
        return self._cache[key]
    
    def set(self, key: str, value: Any) -> bool:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            
        Returns:
            bool: Always True for memory cache
        """
        self._cache[key] = value
        self._timestamps[key] = time.time()
        return True
    
    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if deleted, False if not found
        """
        if key in self._cache:
            del self._cache[key]
            del self._timestamps[key]
            return True
        return False
    
    def clear(self) -> bool:
        """
        Clear all entries from the cache.
        
        Returns:
            bool: Always True for memory cache
        """
        self._cache = {}
        self._timestamps = {}
        return True
    
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
        stats["entries"] = len(self._cache)
        return stats