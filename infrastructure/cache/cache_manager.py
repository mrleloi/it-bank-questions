"""Cache manager implementation."""

import json
import hashlib
from typing import Optional, Any, Dict
from datetime import datetime, timedelta

from .redis_cache import RedisCache
from .memory_cache import MemoryCache


class CacheManager:
    """Multi-layer cache manager."""

    def __init__(
            self,
            memory_cache: Optional[MemoryCache] = None,
            redis_cache: Optional[RedisCache] = None
    ):
        self.memory = memory_cache or MemoryCache()
        self.redis = redis_cache

    def generate_key(self, prefix: str, **kwargs) -> str:
        """Generate cache key from prefix and parameters."""
        params = json.dumps(kwargs, sort_keys=True, default=str)
        hash_digest = hashlib.md5(params.encode()).hexdigest()[:8]
        return f"{prefix}:{hash_digest}"

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        # Check memory cache first
        value = await self.memory.get(key)
        if value is not None:
            return value

        # Check Redis if available
        if self.redis:
            value = await self.redis.get(key)
            if value is not None:
                # Store in memory for next time
                await self.memory.set(key, value, ttl=60)
                return value

        return None

    async def set(
            self,
            key: str,
            value: Any,
            ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache."""
        # Set in memory cache
        await self.memory.set(key, value, ttl=ttl or 300)

        # Set in Redis if available
        if self.redis:
            await self.redis.set(key, value, ttl=ttl or 3600)

        return True

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        memory_deleted = await self.memory.delete(key)
        redis_deleted = True

        if self.redis:
            redis_deleted = await self.redis.delete(key)

        return memory_deleted or redis_deleted

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if await self.memory.exists(key):
            return True

        if self.redis and await self.redis.exists(key):
            return True

        return False

    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern."""
        count = await self.memory.invalidate_pattern(pattern)

        if self.redis:
            count += await self.redis.invalidate_pattern(pattern)

        return count

    async def get_many(self, keys: list[str]) -> Dict[str, Any]:
        """Get multiple values from cache."""
        result = {}

        # Get from memory first
        for key in keys:
            value = await self.memory.get(key)
            if value is not None:
                result[key] = value

        # Get missing keys from Redis
        missing_keys = [k for k in keys if k not in result]
        if missing_keys and self.redis:
            redis_values = await self.redis.get_many(missing_keys)
            result.update(redis_values)

            # Store Redis values in memory
            for key, value in redis_values.items():
                await self.memory.set(key, value, ttl=60)

        return result

    async def set_many(
            self,
            data: Dict[str, Any],
            ttl: Optional[int] = None
    ) -> bool:
        """Set multiple values in cache."""
        # Set in memory
        for key, value in data.items():
            await self.memory.set(key, value, ttl=ttl or 300)

        # Set in Redis
        if self.redis:
            await self.redis.set_many(data, ttl=ttl or 3600)

        return True
