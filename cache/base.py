"""
Base cache interface for taskspec.
"""

import abc
import time
from typing import Any, Dict, Optional, Tuple

class CacheInterface(abc.ABC):
    """Abstract base class for cache implementations."""
    
    def __init__(self, ttl: int = 86400):
        """
        Initialize cache interface.
        
        Args:
            ttl: Time-to-live for cache entries in seconds (default: 24 hours)
        """
        self.ttl = ttl
        self.stats = {
            "hits": 0,
            "misses": 0
        }
    
    @abc.abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            The cached value or None if not found
        """
        pass
    
    @abc.abstractmethod
    def set(self, key: str, value: Any) -> bool:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            
        Returns:
            bool: Success status
        """
        pass
    
    @abc.abstractmethod
    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            bool: Success status
        """
        pass
    
    @abc.abstractmethod
    def clear(self) -> bool:
        """
        Clear all entries from the cache.
        
        Returns:
            bool: Success status
        """
        pass
    
    @abc.abstractmethod
    def get_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.
        
        Returns:
            Dict with cache statistics
        """
        pass
    
    def generate_key(self, prompt: str, model: str, temperature: float) -> str:
        """
        Generate a cache key based on inputs.
        
        Args:
            prompt: The prompt text
            model: The model name
            temperature: The temperature value
            
        Returns:
            str: Cache key
        """
        import hashlib
        # Create a string containing all relevant parameters
        key_input = f"{prompt}|{model}|{temperature}"
        # Generate a hash
        return hashlib.md5(key_input.encode()).hexdigest()
    
    def is_fresh(self, timestamp: float) -> bool:
        """
        Check if a cache entry is still fresh based on its timestamp.
        
        Args:
            timestamp: Entry timestamp
            
        Returns:
            bool: True if entry is still fresh
        """
        return time.time() - timestamp < self.ttl
