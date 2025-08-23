"""Base repository implementation."""

from typing import Generic, TypeVar, Optional, List, Any
from uuid import UUID
from abc import ABC

from django.db import models
from django.core.paginator import Paginator

from domain.repositories.base import Repository, Specification
from infrastructure.cache import CacheManager

T = TypeVar('T')
M = TypeVar('M', bound=models.Model)


class DjangoRepository(Repository[T], Generic[T, M], ABC):
    """Base Django repository implementation."""

    def __init__(self, model_class: type[M], cache_manager: Optional[CacheManager] = None):
        self.model_class = model_class
        self.cache = cache_manager

    async def get_by_id(self, id: UUID) -> Optional[T]:
        """Get entity by ID."""
        # Check cache first
        if self.cache:
            cache_key = f"{self.model_class.__name__}:{id}"
            cached = await self.cache.get(cache_key)
            if cached:
                return self._to_entity(cached)

        try:
            model = await self.model_class.objects.aget(id=id)
            entity = self._to_entity(model)

            # Cache the result
            if self.cache:
                await self.cache.set(cache_key, model, ttl=3600)

            return entity
        except self.model_class.DoesNotExist:
            return None

    async def get_all(
            self,
            limit: Optional[int] = None,
            offset: Optional[int] = None
    ) -> List[T]:
        """Get all entities with pagination."""
        queryset = self.model_class.objects.all()

        if offset:
            queryset = queryset[offset:]
        if limit:
            queryset = queryset[:limit]

        models = [m async for m in queryset]
        return [self._to_entity(m) for m in models]

    async def save(self, entity: T) -> T:
        """Save entity."""
        model = self._to_model(entity)
        await model.asave()

        # Invalidate cache
        if self.cache:
            cache_key = f"{self.model_class.__name__}:{model.id}"
            await self.cache.delete(cache_key)

        return self._to_entity(model)

    async def delete(self, id: UUID) -> bool:
        """Delete entity by ID."""
        try:
            model = await self.model_class.objects.aget(id=id)
            await model.adelete()

            # Invalidate cache
            if self.cache:
                cache_key = f"{self.model_class.__name__}:{id}"
                await self.cache.delete(cache_key)

            return True
        except self.model_class.DoesNotExist:
            return False

    async def exists(self, id: UUID) -> bool:
        """Check if entity exists."""
        return await self.model_class.objects.filter(id=id).aexists()

    async def count(self, specification: Optional[Specification] = None) -> int:
        """Count entities matching specification."""
        queryset = self.model_class.objects.all()

        if specification:
            # Apply specification filtering
            queryset = self._apply_specification(queryset, specification)

        return await queryset.acount()

    async def find(self, specification: Specification) -> List[T]:
        """Find entities matching specification."""
        queryset = self._apply_specification(
            self.model_class.objects.all(),
            specification
        )

        models = [m async for m in queryset]
        return [self._to_entity(m) for m in models]

    def _apply_specification(self, queryset, specification: Specification):
        """Apply specification to queryset."""
        # This would need to be implemented based on specification type
        return queryset

    def _to_entity(self, model: M) -> T:
        """Convert model to entity."""
        raise NotImplementedError

    def _to_model(self, entity: T) -> M:
        """Convert entity to model."""
        raise NotImplementedError
