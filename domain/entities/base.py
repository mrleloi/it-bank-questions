"""Base entity classes."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, KW_ONLY
from datetime import datetime
from typing import List, Optional, Any, Dict
from uuid import UUID, uuid4

from domain.events import DomainEvent


@dataclass(kw_only=True)
class Entity(ABC):
    """Base class for all entities."""
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __eq__(self, other: Any) -> bool:
        """Entities are equal if they have the same ID."""
        if not isinstance(other, Entity):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on ID."""
        return hash(self.id)

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now()

    @abstractmethod
    def validate(self) -> None:
        """Validate entity state."""
        pass

    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary."""
        return {
            'id': str(self.id),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }


@dataclass
class AggregateRoot(Entity):
    """Base class for aggregate roots."""

    def __init__(self):
        self._domain_events: List['DomainEvent'] = field(default_factory=list, init=False, repr=False)
        self.version: int = field(default=1)

    def add_domain_event(self, event: 'DomainEvent') -> None:
        """Add a domain event."""
        self._domain_events.append(event)

    def clear_domain_events(self) -> List['DomainEvent']:
        """Clear and return domain events."""
        events = self._domain_events.copy()
        self._domain_events.clear()
        return events

    def increment_version(self) -> None:
        """Increment the version for optimistic locking."""
        self.version += 1
        self.update_timestamp()
