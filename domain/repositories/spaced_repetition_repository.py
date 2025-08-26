
from abc import abstractmethod
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from .base import Repository


class SpacedRepetitionRepository(Repository):
    """Repository interface for SpacedRepetitionCard."""

    @abstractmethod
    async def get_by_user_and_question(
            self,
            user_id: UUID,
            question_id: UUID
    ) -> Optional['SpacedRepetitionCard']:
        """Get card by user and question."""
        pass

    @abstractmethod
    async def get_due_cards(
            self,
            user_id: UUID,
            facet_id: Optional[UUID] = None,
            limit: Optional[int] = None
    ) -> List['SpacedRepetitionCard']:
        """Get cards due for review."""
        pass

    @abstractmethod
    async def get_new_cards(
            self,
            user_id: UUID,
            facet_id: Optional[UUID] = None,
            limit: Optional[int] = None
    ) -> List['SpacedRepetitionCard']:
        """Get new cards."""
        pass
