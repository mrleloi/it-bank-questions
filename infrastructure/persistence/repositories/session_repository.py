"""Learning session repository implementation."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta

from django.db.models.aggregates import Count, Sum
from django.db.models.query_utils import Q

from domain.entities import LearningSession
from domain.entities.learning_session import SessionMetrics, SessionStatus
from domain.repositories.base import Repository
from infrastructure.persistence.models import LearningSessionModel
from .base import DjangoRepository


class DjangoSessionRepository(DjangoRepository[LearningSession, LearningSessionModel]):
    """Django implementation of SessionRepository."""

    def __init__(self, cache_manager=None):
        super().__init__(LearningSessionModel, cache_manager)

    async def get_active_session(self, user_id: UUID) -> Optional[LearningSession]:
        """Get active session for user."""
        try:
            model = await LearningSessionModel.objects.aget(
                user_id=user_id,
                status='active'
            )
            return self._to_entity(model)
        except LearningSessionModel.DoesNotExist:
            return None

    async def get_user_sessions(
            self,
            user_id: UUID,
            limit: Optional[int] = None,
            offset: Optional[int] = None
    ) -> List[LearningSession]:
        """Get user's sessions."""
        queryset = LearningSessionModel.objects.filter(
            user_id=user_id
        ).order_by('-started_at')

        if offset:
            queryset = queryset[offset:]
        if limit:
            queryset = queryset[:limit]

        models = [m async for m in queryset]
        return [self._to_entity(m) for m in models]

    async def get_sessions_in_period(
            self,
            user_id: UUID,
            start_date: datetime,
            end_date: datetime
    ) -> List[LearningSession]:
        """Get sessions within date range."""
        queryset = LearningSessionModel.objects.filter(
            user_id=user_id,
            started_at__gte=start_date,
            started_at__lte=end_date
        ).order_by('-started_at')

        models = [m async for m in queryset]
        return [self._to_entity(m) for m in models]

    async def get_expired_sessions(
            self,
            before: Optional[datetime] = None
    ) -> List[LearningSession]:
        """Get expired sessions."""
        if not before:
            before = datetime.now() - timedelta(minutes=30)

        queryset = LearningSessionModel.objects.filter(
            status='active',
            last_activity_at__lt=before
        )

        models = [m async for m in queryset]
        return [self._to_entity(m) for m in models]

    async def count_sessions_today(self, user_id: UUID) -> int:
        """Count sessions started today."""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return await LearningSessionModel.objects.filter(
            user_id=user_id,
            started_at__gte=today_start
        ).acount()

    async def get_session_statistics(
            self,
            user_id: UUID,
            period_days: int = 30
    ) -> dict:
        """Get session statistics for user."""
        start_date = datetime.now() - timedelta(days=period_days)
        
        sessions = await LearningSessionModel.objects.filter(
            user_id=user_id,
            started_at__gte=start_date
        ).aaggregate(
            total_sessions=Count('id'),
            completed_sessions=Count('id', filter=Q(status='completed')),
            total_time=Sum('total_time_seconds'),
            total_questions=Sum('answered_questions_count'),
            total_correct=Sum('correct_answers')
        )

        return {
            'total_sessions': sessions['total_sessions'] or 0,
            'completed_sessions': sessions['completed_sessions'] or 0,
            'completion_rate': (
                (sessions['completed_sessions'] / sessions['total_sessions']) * 100
                if sessions['total_sessions'] > 0 else 0
            ),
            'total_time_seconds': sessions['total_time'] or 0,
            'total_questions_answered': sessions['total_questions'] or 0,
            'total_correct_answers': sessions['total_correct'] or 0,
            'accuracy_rate': (
                (sessions['total_correct'] / sessions['total_questions']) * 100
                if sessions['total_questions'] > 0 else 0
            )
        }

    def _to_entity(self, model: LearningSessionModel) -> LearningSession:
        """Convert model to entity."""
        # Create metrics
        metrics = SessionMetrics(
            total_questions=model.total_questions,
            answered_questions=model.answered_questions_count,
            correct_answers=model.correct_answers,
            total_time_seconds=model.total_time_seconds,
            active_time_seconds=model.active_time_seconds,
            average_time_per_question=model.average_time_per_question,
            accuracy_rate=model.accuracy_rate
        )

        return LearningSession(
            id=model.id,
            user_id=model.user_id,
            facet_id=model.facet_id,
            status=SessionStatus(model.status),
            started_at=model.started_at,
            ended_at=model.ended_at,
            last_activity_at=model.last_activity_at,
            metrics=metrics,
            question_limit=model.question_limit,
            time_limit_minutes=model.time_limit_minutes,
            question_types=model.question_types,
            difficulty_range=(model.difficulty_min, model.difficulty_max),
            question_queue=model.question_queue,
            answered_questions=[UUID(qid) for qid in model.answered_questions],
            current_question_id=model.current_question_id,
            current_question_started_at=model.current_question_started_at,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def _to_model(self, entity: LearningSession) -> LearningSessionModel:
        """Convert entity to model."""
        return LearningSessionModel(
            id=entity.id,
            user_id=entity.user_id,
            facet_id=entity.facet_id,
            status=entity.status.value,
            started_at=entity.started_at,
            ended_at=entity.ended_at,
            last_activity_at=entity.last_activity_at,
            question_limit=entity.question_limit,
            time_limit_minutes=entity.time_limit_minutes,
            question_types=entity.question_types,
            difficulty_min=entity.difficulty_range[0],
            difficulty_max=entity.difficulty_range[1],
            question_queue=entity.question_queue,
            answered_questions=[str(qid) for qid in entity.answered_questions],
            current_question_id=entity.current_question_id,
            current_question_started_at=entity.current_question_started_at,
            total_questions=entity.metrics.total_questions,
            answered_questions_count=entity.metrics.answered_questions,
            correct_answers=entity.metrics.correct_answers,
            total_time_seconds=entity.metrics.total_time_seconds,
            active_time_seconds=entity.metrics.active_time_seconds,
            metrics=entity.metrics.to_dict()
        )