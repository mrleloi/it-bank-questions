"""User repository interface."""

from abc import abstractmethod
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from .base import Repository
from ..entities.user import User


class UserRepository(Repository[User]):
    """Repository for User aggregate."""

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        pass

    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        pass

    @abstractmethod
    async def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email."""
        pass

    @abstractmethod
    async def exists_by_username(self, username: str) -> bool:
        """Check if user exists by username."""
        pass

    @abstractmethod
    async def get_active_users(
            self,
            limit: Optional[int] = None,
            offset: Optional[int] = None
    ) -> List[User]:
        """Get active users."""
        pass

    @abstractmethod
    async def get_users_by_role(
            self,
            role: str,
            limit: Optional[int] = None,
            offset: Optional[int] = None
    ) -> List[User]:
        """Get users by role."""
        pass

    @abstractmethod
    async def update_last_login(self, user_id: UUID, timestamp: datetime) -> bool:
        """Update user's last login timestamp."""
        pass

    @abstractmethod
    async def search_users(
            self,
            query: str,
            limit: Optional[int] = None,
            offset: Optional[int] = None
    ) -> List[User]:
        """Search users by name, email, or username."""
        pass