"""
Cache system for taskspec.
"""

from .base import CacheInterface
from .memory_cache import MemoryCache
from .disk_cache import DiskCache

__all__ = ["CacheInterface", "MemoryCache", "DiskCache", "get_cache_manager"]

def get_cache_manager(cache_type="disk", cache_path=None, ttl=86400):
    """
    Factory function to get a cache manager instance.
    
    Args:
        cache_type: Type of cache to use ('memory', 'disk')
        cache_path: Path to cache directory/file (for disk cache)
        ttl: Time-to-live for cache entries in seconds (default: 24 hours)
        
    Returns:
        CacheInterface: Cache manager instance
        
    Raises:
        ValueError: If cache_type is invalid or if cache_path is not provided for disk cache
    """
    if cache_type == "memory":
        return MemoryCache(ttl=ttl)
    elif cache_type == "disk":
        if cache_path is None:
            raise ValueError("cache_path must be provided for disk cache")
        return DiskCache(cache_path=cache_path, ttl=ttl)
    else:
        raise ValueError(f"Unsupported cache type: {cache_type}")
