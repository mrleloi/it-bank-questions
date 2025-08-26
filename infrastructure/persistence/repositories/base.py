from typing import Generic, TypeVar, Optional, List, Any
from uuid import UUID
from abc import ABC

from django.db import models
from asgiref.sync import sync_to_async
from django.db.models import Prefetch

from domain.repositories.base import Repository, Specification
from infrastructure.cache import CacheManager

T = TypeVar('T')
M = TypeVar('M', bound=models.Model)


class DjangoRepository(Generic[T, M], Repository[T], ABC):
    """Base Django repository implementation with proper async/sync handling."""

    def __init__(self, model_class: type[M], cache_manager: Optional[CacheManager] = None):
        self.model_class = model_class
        self.cache = cache_manager

    async def get_by_id(self, id: UUID, load_relationship: bool = True) -> Optional[T]:
        """Get entity by ID with proper async handling."""
        # Check cache first
        if self.cache:
            cache_key = f"{self.model_class.__name__}:{id}"
            cached = await self.cache.get(cache_key)
            if cached:
                # Convert cached model to entity using sync_to_async
                return await sync_to_async(self._to_entity)(cached, load_relationship)

        try:
            # Use sync_to_async for the entire database operation
            model = await self._get_model_by_id(id, load_relationship)
            if not model:
                return None
                
            # Convert to entity in sync context
            entity = await sync_to_async(self._to_entity)(model, load_relationship)

            # Cache the result
            if self.cache and model:
                await self.cache.set(cache_key, model, ttl=3600)

            return entity
        except self.model_class.DoesNotExist:
            return None

    @sync_to_async
    def _get_model_by_id(self, id: UUID, load_relationship: bool) -> Optional[M]:
        """Get model by ID with optional relationship loading."""
        try:
            queryset = self.model_class.objects.filter(id=id)
            if load_relationship:
                queryset = self._apply_select_related(queryset)
                queryset = self._apply_prefetch_related(queryset)
            return queryset.first()
        except self.model_class.DoesNotExist:
            return None

    def _apply_select_related(self, queryset):
        """Apply select_related for ForeignKey and OneToOne relationships.
        Override in subclasses to specify which relationships to load."""
        return queryset

    def _apply_prefetch_related(self, queryset):
        """Apply prefetch_related for ManyToMany and reverse ForeignKey relationships.
        Override in subclasses to specify which relationships to load."""
        return queryset

    async def get_all(
            self,
            limit: Optional[int] = None,
            offset: Optional[int] = None,
            load_relationship: bool = True
    ) -> List[T]:
        """Get all entities with pagination."""
        models = await self._get_all_models(limit, offset, load_relationship)
        # Convert models to entities in sync context
        entities = []
        for model in models:
            entity = await sync_to_async(self._to_entity)(model, load_relationship)
            entities.append(entity)
        return entities

    @sync_to_async
    def _get_all_models(
            self,
            limit: Optional[int],
            offset: Optional[int],
            load_relationship: bool
    ) -> List[M]:
        """Get all models with proper sync handling."""
        queryset = self.model_class.objects.all()
        
        if load_relationship:
            queryset = self._apply_select_related(queryset)
            queryset = self._apply_prefetch_related(queryset)

        if offset:
            queryset = queryset[offset:]
        if limit:
            queryset = queryset[:limit]

        return list(queryset)

    async def save(self, entity: T, load_relationship: bool = True) -> T:
        """Save entity with proper async handling."""
        entity_id = getattr(entity, 'id', None)

        if entity_id:
            # Update existing entity
            saved_model = await self._update_model(entity)
        else:
            # Create new entity
            saved_model = await self._create_model(entity)

        # Invalidate cache if exists
        if self.cache and entity_id:
            cache_key = f"{self.model_class.__name__}:{entity_id}"
            await self.cache.delete(cache_key)

        # Convert back to entity
        return await sync_to_async(self._to_entity)(saved_model, load_relationship)

    @sync_to_async
    def _update_model(self, entity: T) -> M:
        """Update existing model in sync context."""
        entity_id = getattr(entity, 'id')
        try:
            model = self.model_class.objects.get(id=entity_id)
            model = self._update_model_from_entity(model, entity)
            model.save()
            return model
        except self.model_class.DoesNotExist:
            # If doesn't exist, create new
            model = self._to_model(entity)
            model.save()
            return model

    @sync_to_async
    def _create_model(self, entity: T) -> M:
        """Create new model in sync context."""
        model = self._to_model(entity)
        model.save()
        return model

    async def delete(self, id: UUID) -> bool:
        """Delete entity by ID."""
        result = await self._delete_model(id)
        
        # Invalidate cache
        if self.cache and result:
            cache_key = f"{self.model_class.__name__}:{id}"
            await self.cache.delete(cache_key)
            
        return result

    @sync_to_async
    def _delete_model(self, id: UUID) -> bool:
        """Delete model in sync context."""
        try:
            model = self.model_class.objects.get(id=id)
            model.delete()
            return True
        except self.model_class.DoesNotExist:
            return False

    async def exists(self, id: UUID) -> bool:
        """Check if entity exists."""
        return await sync_to_async(
            self.model_class.objects.filter(id=id).exists
        )()

    async def count(self, specification: Optional[Specification] = None) -> int:
        """Count entities matching specification."""
        return await self._count_with_specification(specification)

    @sync_to_async
    def _count_with_specification(self, specification: Optional[Specification]) -> int:
        """Count in sync context."""
        queryset = self.model_class.objects.all()
        if specification:
            queryset = self._apply_specification(queryset, specification)
        return queryset.count()

    async def find(self, specification: Specification) -> List[T]:
        """Find entities matching specification."""
        models = await self._find_with_specification(specification)
        entities = []
        for model in models:
            entity = await sync_to_async(self._to_entity)(model, True)
            entities.append(entity)
        return entities

    @sync_to_async
    def _find_with_specification(self, specification: Specification) -> List[M]:
        """Find models in sync context."""
        queryset = self._apply_specification(
            self.model_class.objects.all(),
            specification
        )
        return list(queryset)

    def _apply_specification(self, queryset, specification: Specification):
        """Apply specification to queryset. Override in subclasses."""
        return queryset

    def _update_model_from_entity(self, model: M, entity: T) -> M:
        """Update existing model with entity data.
        This runs in sync context, so it's safe to access relationships."""
        entity_dict = self._entity_to_dict(entity)
        for field_name, value in entity_dict.items():
            if hasattr(model, field_name):
                setattr(model, field_name, value)
        return model

    def _entity_to_dict(self, entity: T) -> dict:
        """Convert entity to dictionary. Override in subclasses for custom handling."""
        result = {}
        for attr_name in dir(entity):
            if not attr_name.startswith('_') and not callable(getattr(entity, attr_name)):
                value = getattr(entity, attr_name)
                if value is not None:
                    result[attr_name] = value
        return result

    def _to_entity(self, model: M, load_relationship: bool = True) -> T:
        """Convert model to entity. 
        This method runs in SYNC context via sync_to_async,
        so it's safe to access Django ORM relationships here."""
        raise NotImplementedError

    def _to_model(self, entity: T) -> M:
        """Convert entity to model.
        This method runs in SYNC context via sync_to_async."""
        raise NotImplementedError