"""In-memory cache implementation."""

import asyncio
import time
from typing import Optional, Any, Dict
from threading import Lock
from collections import OrderedDict


class MemoryCache:
    """Thread-safe in-memory LRU cache."""

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict = OrderedDict()
        self._expire_times: Dict[str, float] = {}
        self._lock = Lock()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            # Check if key exists and not expired
            if key not in self._cache:
                return None

            # Check expiration
            if key in self._expire_times:
                if time.time() > self._expire_times[key]:
                    # Expired, remove it
                    del self._cache[key]
                    del self._expire_times[key]
                    return None

            # Move to end (most recently used)
            value = self._cache.pop(key)
            self._cache[key] = value
            return value

    async def set(
            self,
            key: str,
            value: Any,
            ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache."""
        with self._lock:
            # Remove oldest items if at capacity
            while len(self._cache) >= self.max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                if oldest_key in self._expire_times:
                    del self._expire_times[oldest_key]

            # Set value
            self._cache[key] = value

            # Set expiration time
            expire_ttl = ttl or self.default_ttl
            if expire_ttl > 0:
                self._expire_times[key] = time.time() + expire_ttl

            return True

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                if key in self._expire_times:
                    del self._expire_times[key]
                return True
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        value = await self.get(key)
        return value is not None

    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate keys matching pattern."""
        with self._lock:
            keys_to_remove = [
                key for key in self._cache.keys()
                if pattern in key
            ]

            for key in keys_to_remove:
                del self._cache[key]
                if key in self._expire_times:
                    del self._expire_times[key]

            return len(keys_to_remove)

    async def clear(self) -> bool:
        """Clear all cache."""
        with self._lock:
            self._cache.clear()
            self._expire_times.clear()
            return True

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'keys': list(self._cache.keys())
            }