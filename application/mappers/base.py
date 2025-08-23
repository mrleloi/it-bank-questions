"""Base mapper class."""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic

TEntity = TypeVar('TEntity')
TDto = TypeVar('TDto')


class Mapper(ABC, Generic[TEntity, TDto]):
    """Base mapper for converting between entities and DTOs."""

    @abstractmethod
    def to_dto(self, entity: TEntity) -> TDto:
        """Convert entity to DTO."""
        pass

    @abstractmethod
    def to_entity(self, dto: TDto) -> TEntity:
        """Convert DTO to entity."""
        pass