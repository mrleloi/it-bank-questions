"""Base repository interface."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

T = TypeVar('T')


class Specification(ABC):
    """Specification pattern for complex queries."""

    @abstractmethod
    def is_satisfied_by(self, candidate: T) -> bool:
        """Check if candidate satisfies specification."""
        pass

    def and_(self, other: 'Specification') -> 'AndSpecification':
        """Combine with AND logic."""
        return AndSpecification(self, other)

    def or_(self, other: 'Specification') -> 'OrSpecification':
        """Combine with OR logic."""
        return OrSpecification(self, other)

    def not_(self) -> 'NotSpecification':
        """Negate specification."""
        return NotSpecification(self)


class AndSpecification(Specification):
    """AND combination of specifications."""

    def __init__(self, left: Specification, right: Specification):
        self.left = left
        self.right = right

    def is_satisfied_by(self, candidate: T) -> bool:
        return (
            self.left.is_satisfied_by(candidate) and
            self.right.is_satisfied_by(candidate)
        )


class OrSpecification(Specification):
    """OR combination of specifications."""

    def __init__(self, left: Specification, right: Specification):
        self.left = left
        self.right = right

    def is_satisfied_by(self, candidate: T) -> bool:
        return (
            self.left.is_satisfied_by(candidate) or
            self.right.is_satisfied_by(candidate)
        )


class NotSpecification(Specification):
    """NOT specification."""

    def __init__(self, spec: Specification):
        self.spec = spec

    def is_satisfied_by(self, candidate: T) -> bool:
        return not self.spec.is_satisfied_by(candidate)


class Repository(ABC, Generic[T]):
    """Base repository interface."""

    @abstractmethod
    async def get_by_id(self, id: UUID) -> Optional[T]:
        """Get entity by ID."""
        pass

    @abstractmethod
    async def get_all(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[T]:
        """Get all entities with pagination."""
        pass

    @abstractmethod
    async def find(self, specification: Specification) -> List[T]:
        """Find entities matching specification."""
        pass

    @abstractmethod
    async def save(self, entity: T) -> T:
        """Save entity (create or update)."""
        pass

    @abstractmethod
    async def delete(self, id: UUID) -> bool:
        """Delete entity by ID."""
        pass

    @abstractmethod
    async def exists(self, id: UUID) -> bool:
        """Check if entity exists."""
        pass

    @abstractmethod
    async def count(self, specification: Optional[Specification] = None) -> int:
        """Count entities matching specification."""
        pass