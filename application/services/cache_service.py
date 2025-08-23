"""Cache service interface."""

from abc import ABC, abstractmethod
from typing import Optional, Any


class CacheService(ABC):
    """Abstract cache service."""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass

    @abstractmethod
    async def set(
            self,
            key: str,
            value: Any,
            ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        pass

    @abstractmethod
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate keys matching pattern."""
        pass