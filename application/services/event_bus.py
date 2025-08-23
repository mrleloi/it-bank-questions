"""Event bus for domain events."""

from abc import ABC, abstractmethod
from typing import List

from domain.events import DomainEvent


class EventBus(ABC):
    """Abstract event bus."""

    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """Publish a domain event."""
        pass

    @abstractmethod
    async def publish_batch(self, events: List[DomainEvent]) -> None:
        """Publish multiple events."""
        pass