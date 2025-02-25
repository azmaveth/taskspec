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
    """
    if cache_type == "memory":
        return MemoryCache(ttl=ttl)
    elif cache_type == "disk":
        return DiskCache(cache_path=cache_path, ttl=ttl)
    else:
        raise ValueError(f"Unsupported cache type: {cache_type}")
