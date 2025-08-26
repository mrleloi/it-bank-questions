from abc import abstractmethod
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from .base import Repository


class EventRepository(Repository):
    """Repository interface for LearningEvent."""

    @abstractmethod
    async def get_user_events(
            self,
            user_id: UUID,
            event_type: Optional[str] = None,
            start_date: Optional[datetime] = None,
            limit: Optional[int] = None
    ) -> List['LearningEvent']:
        """Get events for a user."""
        pass

    @abstractmethod
    async def get_events_by_type(
            self,
            event_type: str,
            start_date: Optional[datetime] = None,
            limit: Optional[int] = None
    ) -> List['LearningEvent']:
        """Get events by type."""
        pass