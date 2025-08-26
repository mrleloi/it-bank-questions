"""Event repository implementation."""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta

from django.db.models import Q, Count
from django.db.models.functions import TruncDate, TruncHour

from domain.entities import LearningEvent
from domain.entities.learning_event import EventType
from domain.repositories.base import Repository
from infrastructure.persistence.models import LearningEventModel
from .base import DjangoRepository


class DjangoEventRepository(DjangoRepository[LearningEvent, LearningEventModel]):
    """Django implementation of EventRepository."""

    def __init__(self, cache_manager=None):
        super().__init__(LearningEventModel, cache_manager)

    async def get_user_events(
            self,
            user_id: UUID,
            event_type: Optional[EventType] = None,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None,
            limit: Optional[int] = None
    ) -> List[LearningEvent]:
        """Get events for a user."""
        queryset = LearningEventModel.objects.filter(user_id=user_id)

        if event_type:
            queryset = queryset.filter(event_type=event_type.value)

        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)

        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)

        queryset = queryset.order_by('-created_at')

        if limit:
            queryset = queryset[:limit]

        models = [m async for m in queryset]
        return [self._to_entity(m) for m in models]

    async def get_events_by_type(
            self,
            event_type: Optional[EventType] = None,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None,
            limit: Optional[int] = None
    ) -> List[LearningEvent]:
        """Get events by type."""
        queryset = LearningEventModel.objects.all()

        if event_type:
            queryset = queryset.filter(event_type=event_type.value)

        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)

        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)

        queryset = queryset.order_by('-created_at')

        if limit:
            queryset = queryset[:limit]

        models = [m async for m in queryset]
        return [self._to_entity(m) for m in models]

    async def get_session_events(
            self,
            session_id: UUID,
            event_types: Optional[List[EventType]] = None
    ) -> List[LearningEvent]:
        """Get events for a specific session."""
        queryset = LearningEventModel.objects.filter(session_id=session_id)

        if event_types:
            type_values = [et.value for et in event_types]
            queryset = queryset.filter(event_type__in=type_values)

        queryset = queryset.order_by('created_at')
        models = [m async for m in queryset]
        return [self._to_entity(m) for m in models]

    async def get_question_events(
            self,
            question_id: UUID,
            event_types: Optional[List[EventType]] = None,
            start_date: Optional[datetime] = None
    ) -> List[LearningEvent]:
        """Get events for a specific question."""
        queryset = LearningEventModel.objects.filter(question_id=question_id)

        if event_types:
            type_values = [et.value for et in event_types]
            queryset = queryset.filter(event_type__in=type_values)

        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)

        queryset = queryset.order_by('-created_at')
        models = [m async for m in queryset]
        return [self._to_entity(m) for m in models]

    async def get_facet_events(
            self,
            facet_id: UUID,
            event_types: Optional[List[EventType]] = None,
            user_id: Optional[UUID] = None,
            start_date: Optional[datetime] = None
    ) -> List[LearningEvent]:
        """Get events for a specific facet."""
        queryset = LearningEventModel.objects.filter(facet_id=facet_id)

        if event_types:
            type_values = [et.value for et in event_types]
            queryset = queryset.filter(event_type__in=type_values)

        if user_id:
            queryset = queryset.filter(user_id=user_id)

        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)

        queryset = queryset.order_by('-created_at')
        models = [m async for m in queryset]
        return [self._to_entity(m) for m in models]

    async def get_achievement_events(
            self,
            user_id: Optional[UUID] = None,
            achievement_name: Optional[str] = None
    ) -> List[LearningEvent]:
        """Get achievement unlock events."""
        queryset = LearningEventModel.objects.filter(
            event_type=EventType.ACHIEVEMENT_UNLOCKED.value
        )

        if user_id:
            queryset = queryset.filter(user_id=user_id)

        if achievement_name:
            queryset = queryset.filter(
                event_data__achievement_name=achievement_name
            )

        queryset = queryset.order_by('-created_at')
        models = [m async for m in queryset]
        return [self._to_entity(m) for m in models]

    async def get_daily_activity(
            self,
            user_id: UUID,
            days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get daily activity statistics."""
        start_date = datetime.now() - timedelta(days=days)
        
        activity = await LearningEventModel.objects.filter(
            user_id=user_id,
            created_at__gte=start_date,
            event_type__in=[
                EventType.QUESTION_ANSWERED.value,
                EventType.SESSION_STARTED.value,
                EventType.SESSION_COMPLETED.value
            ]
        ).extra(
            select={'date': 'DATE(created_at)'}
        ).values('date').annotate(
            sessions_started=Count('id', filter=Q(event_type=EventType.SESSION_STARTED.value)),
            questions_answered=Count('id', filter=Q(event_type=EventType.QUESTION_ANSWERED.value)),
            sessions_completed=Count('id', filter=Q(event_type=EventType.SESSION_COMPLETED.value))
        ).order_by('date')

        return list(activity)

    async def get_hourly_activity(
            self,
            user_id: UUID,
            days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get hourly activity patterns."""
        start_date = datetime.now() - timedelta(days=days)
        
        activity = await LearningEventModel.objects.filter(
            user_id=user_id,
            created_at__gte=start_date,
            event_type__in=[
                EventType.QUESTION_ANSWERED.value,
                EventType.SESSION_STARTED.value
            ]
        ).extra(
            select={'hour': 'EXTRACT(hour FROM created_at)'}
        ).values('hour').annotate(
            activity_count=Count('id')
        ).order_by('hour')

        return list(activity)

    async def get_event_statistics(
            self,
            user_id: Optional[UUID] = None,
            start_date: Optional[datetime] = None,
            event_types: Optional[List[EventType]] = None
    ) -> Dict[str, Any]:
        """Get event statistics."""
        queryset = LearningEventModel.objects.all()

        if user_id:
            queryset = queryset.filter(user_id=user_id)

        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)

        if event_types:
            type_values = [et.value for et in event_types]
            queryset = queryset.filter(event_type__in=type_values)

        # Get counts by event type
        event_counts = await queryset.values('event_type').annotate(
            count=Count('id')
        ).order_by('-count')

        # Get daily counts for the last 30 days
        thirty_days_ago = datetime.now() - timedelta(days=30)
        daily_counts = await queryset.filter(
            created_at__gte=thirty_days_ago
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')

        return {
            'total_events': await queryset.acount(),
            'event_type_distribution': list(event_counts),
            'daily_activity': list(daily_counts),
            'unique_users': await queryset.values('user_id').distinct().acount() if not user_id else 1
        }

    async def cleanup_old_events(self, days_to_keep: int = 365) -> int:
        """Cleanup old events (keep only recent ones)."""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # Keep important events longer
        important_events = [
            EventType.ACHIEVEMENT_UNLOCKED.value,
            EventType.FACET_MASTERED.value,
            EventType.USER_REGISTERED.value
        ]

        deleted_count, _ = await LearningEventModel.objects.filter(
            created_at__lt=cutoff_date
        ).exclude(
            event_type__in=important_events
        ).adelete()

        return deleted_count

    def _to_entity(self, model: LearningEventModel) -> LearningEvent:
        """Convert model to entity."""
        return LearningEvent(
            id=model.id,
            user_id=model.user_id,
            event_type=EventType(model.event_type),
            event_data=model.event_data,
            session_id=model.session_id,
            question_id=model.question_id,
            facet_id=model.facet_id,
            ip_address=model.ip_address,
            user_agent=model.user_agent,
            device_type=model.device_type,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def _to_model(self, entity: LearningEvent) -> LearningEventModel:
        """Convert entity to model."""
        return LearningEventModel(
            id=entity.id,
            user_id=entity.user_id,
            event_type=entity.event_type.value,
            event_data=entity.event_data,
            session_id=entity.session_id,
            question_id=entity.question_id,
            facet_id=entity.facet_id,
            ip_address=entity.ip_address,
            user_agent=entity.user_agent,
            device_type=entity.device_type
        )