"""Progress repository implementation."""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta

from django.db.models import Q, Count, Avg, Sum, Max

from domain.entities import UserProgress, FacetProgress
from domain.value_objects import MasteryLevel
from domain.repositories.base import Repository
from infrastructure.persistence.models import UserProgressModel, FacetProgressModel
from .base import DjangoRepository


class DjangoProgressRepository(DjangoRepository[UserProgress, UserProgressModel]):
    """Django implementation of ProgressRepository."""

    def __init__(self, cache_manager=None):
        super().__init__(UserProgressModel, cache_manager)

    async def get_user_progress(self, user_id: UUID) -> Optional[UserProgress]:
        """Get overall user progress."""
        try:
            model = await UserProgressModel.objects.aget(user_id=user_id)
            
            # Get facet progresses
            facet_models = FacetProgressModel.objects.filter(user_id=user_id)
            facet_progresses = {}
            
            async for facet_model in facet_models:
                facet_progress = self._facet_model_to_entity(facet_model)
                facet_progresses[facet_progress.facet_id] = facet_progress

            return UserProgress(
                id=model.id,
                user_id=model.user_id,
                facet_progresses=facet_progresses,
                total_study_time_seconds=model.total_study_time_seconds,
                total_questions_answered=model.total_questions_answered,
                total_correct_answers=model.total_correct_answers,
                overall_mastery_score=model.overall_mastery_score,
                achievements_unlocked=model.achievements_unlocked,
                achievement_points=model.achievement_points,
                preferred_study_time=model.preferred_study_time,
                average_session_length_minutes=model.average_session_length_minutes,
                most_productive_day=model.most_productive_day,
                created_at=model.created_at,
                updated_at=model.updated_at
            )
        except UserProgressModel.DoesNotExist:
            # Create new user progress
            return UserProgress(user_id=user_id)

    async def get_facet_progress(
            self,
            user_id: UUID,
            facet_id: UUID
    ) -> Optional[FacetProgress]:
        """Get progress for specific facet."""
        try:
            model = await FacetProgressModel.objects.aget(
                user_id=user_id,
                facet_id=facet_id
            )
            return self._facet_model_to_entity(model)
        except FacetProgressModel.DoesNotExist:
            return None

    async def get_facet_progresses(
            self,
            user_id: UUID,
            mastery_level: Optional[MasteryLevel] = None
    ) -> List[FacetProgress]:
        """Get all facet progresses for user."""
        queryset = FacetProgressModel.objects.filter(user_id=user_id)

        if mastery_level:
            # Filter by mastery level score range
            min_score = mastery_level.minimum_score()
            max_score = 100 if mastery_level == MasteryLevel.EXPERT else min_score + 20
            queryset = queryset.filter(
                mastery_score__gte=min_score,
                mastery_score__lt=max_score
            )

        queryset = queryset.order_by('-last_activity_at')
        models = [m async for m in queryset]
        return [self._facet_model_to_entity(m) for m in models]

    async def get_top_learners(
            self,
            limit: int = 10,
            timeframe: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get top learners by achievement points."""
        queryset = UserProgressModel.objects.select_related('user')

        if timeframe == 'week':
            week_ago = datetime.now() - timedelta(days=7)
            queryset = queryset.filter(updated_at__gte=week_ago)
        elif timeframe == 'month':
            month_ago = datetime.now() - timedelta(days=30)
            queryset = queryset.filter(updated_at__gte=month_ago)

        queryset = queryset.order_by('-achievement_points')[:limit]

        results = []
        async for progress in queryset:
            results.append({
                'user_id': progress.user_id,
                'username': progress.user.username,
                'achievement_points': progress.achievement_points,
                'overall_mastery_score': progress.overall_mastery_score,
                'total_questions_answered': progress.total_questions_answered,
                'achievements_count': len(progress.achievements_unlocked)
            })

        return results

    async def get_global_statistics(self) -> Dict[str, Any]:
        """Get global learning statistics."""
        user_stats = await UserProgressModel.objects.aggregate(
            total_users=Count('id'),
            total_questions_answered=Sum('total_questions_answered'),
            total_study_time=Sum('total_study_time_seconds'),
            average_mastery=Avg('overall_mastery_score'),
            total_achievements=Sum('achievement_points')
        )

        facet_stats = await FacetProgressModel.objects.aggregate(
            active_facets=Count('facet_id', distinct=True),
            average_completion=Avg('completion_percentage'),
            total_mastered=Count('id', filter=Q(mastery_score__gte=80))
        )

        return {
            'total_users': user_stats['total_users'] or 0,
            'total_questions_answered': user_stats['total_questions_answered'] or 0,
            'total_study_time_hours': (user_stats['total_study_time'] or 0) / 3600,
            'average_mastery_score': user_stats['average_mastery'] or 0,
            'total_achievement_points': user_stats['total_achievements'] or 0,
            'active_facets': facet_stats['active_facets'] or 0,
            'average_completion_rate': facet_stats['average_completion'] or 0,
            'total_facets_mastered': facet_stats['total_mastered'] or 0
        }

    async def update_facet_progress(
            self,
            user_id: UUID,
            facet_id: UUID,
            **updates
    ) -> Optional[FacetProgress]:
        """Update facet progress."""
        model, created = await FacetProgressModel.objects.aget_or_create(
            user_id=user_id,
            facet_id=facet_id,
            defaults=updates
        )

        if not created:
            for key, value in updates.items():
                setattr(model, key, value)
            await model.asave()

        return self._facet_model_to_entity(model)

    async def get_streak_statistics(self, user_id: UUID) -> Dict[str, Any]:
        """Get streak statistics for user."""
        facet_progresses = await FacetProgressModel.objects.filter(
            user_id=user_id
        ).aggregate(
            current_max_streak=Max('current_streak_days'),
            longest_max_streak=Max('longest_streak_days'),
            active_streaks=Count('id', filter=Q(current_streak_days__gt=0)),
            total_facets=Count('id')
        )

        return {
            'current_max_streak': facet_progresses['current_max_streak'] or 0,
            'longest_max_streak': facet_progresses['longest_max_streak'] or 0,
            'active_streaks': facet_progresses['active_streaks'] or 0,
            'total_facets': facet_progresses['total_facets'] or 0
        }

    def _facet_model_to_entity(self, model: FacetProgressModel) -> FacetProgress:
        """Convert FacetProgressModel to FacetProgress entity."""
        return FacetProgress(
            id=model.id,
            user_id=model.user_id,
            facet_id=model.facet_id,
            total_questions=model.total_questions,
            seen_questions=model.seen_questions,
            mastered_questions=model.mastered_questions,
            mastery_score=model.mastery_score,
            last_activity_at=model.last_activity_at,
            total_time_spent_seconds=model.total_time_spent_seconds,
            accuracy_rate=model.accuracy_rate,
            average_response_time=model.average_response_time,
            difficulty_comfort=model.difficulty_comfort,
            current_streak_days=model.current_streak_days,
            longest_streak_days=model.longest_streak_days,
            last_streak_date=model.last_streak_date,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def _facet_entity_to_model(self, entity: FacetProgress) -> FacetProgressModel:
        """Convert FacetProgress entity to model."""
        return FacetProgressModel(
            id=entity.id,
            user_id=entity.user_id,
            facet_id=entity.facet_id,
            total_questions=entity.total_questions,
            seen_questions=entity.seen_questions,
            mastered_questions=entity.mastered_questions,
            mastery_score=entity.mastery_score,
            accuracy_rate=entity.accuracy_rate,
            average_response_time=entity.average_response_time,
            difficulty_comfort=entity.difficulty_comfort,
            last_activity_at=entity.last_activity_at,
            total_time_spent_seconds=entity.total_time_spent_seconds,
            current_streak_days=entity.current_streak_days,
            longest_streak_days=entity.longest_streak_days,
            last_streak_date=entity.last_streak_date,
            metrics=getattr(entity, 'metrics', {})
        )

    def _to_entity(self, model: UserProgressModel) -> UserProgress:
        """Convert UserProgressModel to UserProgress entity."""
        return UserProgress(
            id=model.id,
            user_id=model.user_id,
            total_study_time_seconds=model.total_study_time_seconds,
            total_questions_answered=model.total_questions_answered,
            total_correct_answers=model.total_correct_answers,
            overall_mastery_score=model.overall_mastery_score,
            achievements_unlocked=model.achievements_unlocked,
            achievement_points=model.achievement_points,
            preferred_study_time=model.preferred_study_time,
            average_session_length_minutes=model.average_session_length_minutes,
            most_productive_day=model.most_productive_day,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def _to_model(self, entity: UserProgress) -> UserProgressModel:
        """Convert UserProgress entity to model."""
        return UserProgressModel(
            id=entity.id,
            user_id=entity.user_id,
            total_study_time_seconds=entity.total_study_time_seconds,
            total_questions_answered=entity.total_questions_answered,
            total_correct_answers=entity.total_correct_answers,
            overall_mastery_score=entity.overall_mastery_score,
            achievements_unlocked=entity.achievements_unlocked,
            achievement_points=entity.achievement_points,
            preferred_study_time=entity.preferred_study_time,
            average_session_length_minutes=entity.average_session_length_minutes,
            most_productive_day=entity.most_productive_day
        )