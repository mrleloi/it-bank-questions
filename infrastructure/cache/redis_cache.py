"""Redis cache implementation."""

import json
import pickle
from typing import Optional, Any, Dict
import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool


class RedisCache:
    """Redis cache implementation."""

    def __init__(
            self,
            host: str = 'localhost',
            port: int = 6379,
            db: int = 0,
            password: Optional[str] = None,
            pool: Optional[ConnectionPool] = None
    ):
        if pool:
            self.redis = redis.Redis(connection_pool=pool)
        else:
            self.redis = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=False  # We'll handle encoding/decoding
            )

    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis."""
        try:
            value = await self.redis.get(key)
            if value is None:
                return None

            # Try to deserialize
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # Fall back to pickle
                return pickle.loads(value)
        except Exception as e:
            print(f"Redis get error: {e}")
            return None

    async def set(
            self,
            key: str,
            value: Any,
            ttl: Optional[int] = None
    ) -> bool:
        """Set value in Redis."""
        try:
            # Serialize value
            try:
                serialized = json.dumps(value, default=str)
            except (TypeError, ValueError):
                # Fall back to pickle for complex objects
                serialized = pickle.dumps(value)

            if ttl:
                await self.redis.setex(key, ttl, serialized)
            else:
                await self.redis.set(key, serialized)

            return True
        except Exception as e:
            print(f"Redis set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from Redis."""
        try:
            result = await self.redis.delete(key)
            return result > 0
        except Exception as e:
            print(f"Redis delete error: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            print(f"Redis exists error: {e}")
            return False

    async def invalidate_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        try:
            cursor = 0
            count = 0

            while True:
                cursor, keys = await self.redis.scan(
                    cursor,
                    match=f"*{pattern}*",
                    count=100
                )

                if keys:
                    count += await self.redis.delete(*keys)

                if cursor == 0:
                    break

            return count
        except Exception as e:
            print(f"Redis invalidate pattern error: {e}")
            return 0

    async def get_many(self, keys: list[str]) -> Dict[str, Any]:
        """Get multiple values from Redis."""
        try:
            values = await self.redis.mget(keys)
            result = {}

            for key, value in zip(keys, values):
                if value is not None:
                    try:
                        result[key] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        result[key] = pickle.loads(value)

            return result
        except Exception as e:
            print(f"Redis get_many error: {e}")
            return {}

    async def set_many(
            self,
            data: Dict[str, Any],
            ttl: Optional[int] = None
    ) -> bool:
        """Set multiple values in Redis."""
        try:
            pipe = self.redis.pipeline()

            for key, value in data.items():
                try:
                    serialized = json.dumps(value, default=str)
                except (TypeError, ValueError):
                    serialized = pickle.dumps(value)

                if ttl:
                    pipe.setex(key, ttl, serialized)
                else:
                    pipe.set(key, serialized)

            await pipe.execute()
            return True
        except Exception as e:
            print(f"Redis set_many error: {e}")
            return False

    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment a counter."""
        try:
            return await self.redis.incrby(key, amount)
        except Exception as e:
            print(f"Redis increment error: {e}")
            return 0

    async def close(self):
        """Close Redis connection."""
        await self.redis.close()
