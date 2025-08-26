"""Base domain event classes."""

from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID, uuid4


@dataclass(kw_only=True)
class DomainEvent(ABC):
    """Base class for all domain events."""

    event_id: UUID = field(default_factory=uuid4)
    aggregate_id: Optional[UUID] = None
    occurred_at: datetime = field(default_factory=datetime.now)
    version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            'event_id': str(self.event_id),
            'event_type': self.__class__.__name__,
            'aggregate_id': str(self.aggregate_id) if self.aggregate_id else None,
            'occurred_at': self.occurred_at.isoformat(),
            'version': self.version,
            'data': self._get_event_data()
        }
    
    def _get_event_data(self) -> Dict[str, Any]:
        """Get event-specific data. Override in subclasses."""
        return {}


@dataclass(kw_only=True)
class UserDomainEvent(DomainEvent):
    """Base class for user-related domain events."""

    user_id: UUID
    
    def __post_init__(self):
        if self.aggregate_id is None and self.user_id:
            self.aggregate_id = self.user_id


@dataclass(kw_only=True)
class LearningDomainEvent(DomainEvent):
    """Base class for learning-related domain events."""
    
    user_id: UUID = field(default=None)
    session_id: Optional[UUID] = field(default=None)
    question_id: Optional[UUID] = field(default=None)
    facet_id: Optional[UUID] = field(default=None)