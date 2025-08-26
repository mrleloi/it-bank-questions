from abc import abstractmethod
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from .base import Repository


class SessionRepository(Repository):
    """Repository interface for LearningSession."""

    @abstractmethod
    async def get_active_session(self, user_id: UUID) -> Optional['LearningSession']:
        """Get active session for user."""
        pass

    @abstractmethod
    async def get_user_sessions(
            self,
            user_id: UUID,
            limit: Optional[int] = None,
            offset: Optional[int] = None
    ) -> List['LearningSession']:
        """Get user's sessions."""
        pass

    @abstractmethod
    async def get_expired_sessions(
            self,
            before: Optional[datetime] = None
    ) -> List['LearningSession']:
        """Get expired sessions."""
        pass