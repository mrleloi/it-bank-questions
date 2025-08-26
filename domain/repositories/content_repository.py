
from abc import abstractmethod
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from .base import Repository
from ..entities import Facet


class ContentRepository(Repository):
    """Repository interface for Content hierarchy."""

    @abstractmethod
    async def get_facet(self, facet_id: UUID) -> Optional['Facet']:
        """Get facet by ID."""
        pass

    @abstractmethod
    async def ensure_hierarchy(
            self,
            topic_code: str,
            subtopic_code: str,
            leaf_code: str,
            facet_code: str
    ) -> 'Facet':
        """Ensure complete hierarchy exists."""
        pass

    @abstractmethod
    async def search_content(
            self,
            query: str,
            level: Optional[str] = None,
            limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Search content."""
        pass

