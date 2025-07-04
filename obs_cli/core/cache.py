"""Cache manager for query results."""

import hashlib
import time
from typing import Any, Dict, Optional, Tuple
from collections import OrderedDict


class CacheManager:
    """Manages cached query results with TTL and size limits."""
    
    def __init__(self, ttl_seconds: int = 300, max_size: int = 100):
        """Initialize cache manager.
        
        Args:
            ttl_seconds: Time-to-live for cached entries in seconds
            max_size: Maximum number of cached entries
        """
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self._cache: OrderedDict[str, Tuple[Any, float]] = OrderedDict()
        self._hits = 0
        self._misses = 0
    
    def _make_key(self, query: str, vault_path: str) -> str:
        """Create cache key from query and vault path."""
        content = f"{vault_path}:{query}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value if valid.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if valid, None otherwise
        """
        if key not in self._cache:
            self._misses += 1
            return None
        
        value, timestamp = self._cache[key]
        current_time = time.time()
        
        # Check if expired
        if current_time - timestamp > self.ttl_seconds:
            del self._cache[key]
            self._misses += 1
            return None
        
        # Move to end to maintain LRU order
        self._cache.move_to_end(key)
        self._hits += 1
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Store value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        # Remove oldest if at capacity
        if len(self._cache) >= self.max_size and key not in self._cache:
            self._cache.popitem(last=False)
        
        self._cache[key] = (value, time.time())
        self._cache.move_to_end(key)
    
    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        total_requests = self._hits + self._misses
        hit_rate = self._hits / total_requests if total_requests > 0 else 0
        
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
        }