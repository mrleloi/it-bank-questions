from abc import abstractmethod
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from .base import Repository


class ProgressRepository(Repository):
    """Repository interface for UserProgress."""

    @abstractmethod
    async def get_user_progress(self, user_id: UUID) -> Optional['UserProgress']:
        """Get overall user progress."""
        pass

    @abstractmethod
    async def get_facet_progress(
            self,
            user_id: UUID,
            facet_id: UUID
    ) -> Optional['FacetProgress']:
        """Get progress for specific facet."""
        pass

    @abstractmethod
    async def get_top_learners(
            self,
            limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get top learners by points."""
        pass

