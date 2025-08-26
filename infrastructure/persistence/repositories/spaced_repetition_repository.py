"""Spaced repetition repository implementation."""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta

from django.db.models import Q, Count, Avg

from domain.entities import SpacedRepetitionCard, CardStatistics
from domain.value_objects import CardState, ReviewInterval, DifficultyRating
from domain.repositories.base import Repository
from infrastructure.persistence.models import SpacedRepetitionCardModel
from .base import DjangoRepository


class DjangoSpacedRepetitionRepository(DjangoRepository[SpacedRepetitionCard, SpacedRepetitionCardModel]):
    """Django implementation of SpacedRepetitionRepository."""

    def __init__(self, cache_manager=None):
        super().__init__(SpacedRepetitionCardModel, cache_manager)

    async def get_by_user_and_question(
            self,
            user_id: UUID,
            question_id: UUID
    ) -> Optional[SpacedRepetitionCard]:
        """Get card by user and question."""
        try:
            model = await SpacedRepetitionCardModel.objects.aget(
                user_id=user_id,
                question_id=question_id
            )
            return self._to_entity(model)
        except SpacedRepetitionCardModel.DoesNotExist:
            return None

    async def get_due_cards(
            self,
            user_id: UUID,
            facet_id: Optional[UUID] = None,
            limit: Optional[int] = None
    ) -> List[SpacedRepetitionCard]:
        """Get cards due for review."""
        queryset = SpacedRepetitionCardModel.objects.filter(
            user_id=user_id,
            due_date__lte=datetime.now(),
            state__in=['review', 'relearning']
        ).order_by('due_date')

        if facet_id:
            queryset = queryset.filter(question__facet_id=facet_id)

        if limit:
            queryset = queryset[:limit]

        models = [m async for m in queryset]
        return [self._to_entity(m) for m in models]

    async def get_overdue_cards(
            self,
            user_id: UUID,
            facet_id: Optional[UUID] = None,
            limit: Optional[int] = None
    ) -> List[SpacedRepetitionCard]:
        """Get overdue cards."""
        yesterday = datetime.now() - timedelta(days=1)
        
        queryset = SpacedRepetitionCardModel.objects.filter(
            user_id=user_id,
            due_date__lt=yesterday,
            state__in=['review', 'relearning']
        ).order_by('due_date')

        if facet_id:
            queryset = queryset.filter(question__facet_id=facet_id)

        if limit:
            queryset = queryset[:limit]

        models = [m async for m in queryset]
        return [self._to_entity(m) for m in models]

    async def get_learning_cards(
            self,
            user_id: UUID,
            facet_id: Optional[UUID] = None,
            limit: Optional[int] = None
    ) -> List[SpacedRepetitionCard]:
        """Get cards in learning phase."""
        queryset = SpacedRepetitionCardModel.objects.filter(
            user_id=user_id,
            state='learning',
            due_date__lte=datetime.now()
        ).order_by('due_date')

        if facet_id:
            queryset = queryset.filter(question__facet_id=facet_id)

        if limit:
            queryset = queryset[:limit]

        models = [m async for m in queryset]
        return [self._to_entity(m) for m in models]

    async def get_new_cards(
            self,
            user_id: UUID,
            facet_id: Optional[UUID] = None,
            limit: Optional[int] = None
    ) -> List[SpacedRepetitionCard]:
        """Get new cards."""
        queryset = SpacedRepetitionCardModel.objects.filter(
            user_id=user_id,
            state='new'
        ).order_by('created_at')

        if facet_id:
            queryset = queryset.filter(question__facet_id=facet_id)

        if limit:
            queryset = queryset[:limit]

        models = [m async for m in queryset]
        return [self._to_entity(m) for m in models]

    async def get_cards_by_state(
            self,
            user_id: UUID,
            state: CardState,
            facet_id: Optional[UUID] = None,
            limit: Optional[int] = None
    ) -> List[SpacedRepetitionCard]:
        """Get cards by state."""
        queryset = SpacedRepetitionCardModel.objects.filter(
            user_id=user_id,
            state=state.value
        )

        if facet_id:
            queryset = queryset.filter(question__facet_id=facet_id)

        if limit:
            queryset = queryset[:limit]

        models = [m async for m in queryset]
        return [self._to_entity(m) for m in models]

    async def get_leech_cards(
            self,
            user_id: UUID,
            threshold: int = 8
    ) -> List[SpacedRepetitionCard]:
        """Get leech cards (cards with many lapses)."""
        queryset = SpacedRepetitionCardModel.objects.filter(
            user_id=user_id,
            lapses__gte=threshold
        ).order_by('-lapses')

        models = [m async for m in queryset]
        return [self._to_entity(m) for m in models]

    async def get_statistics(
            self,
            user_id: UUID,
            facet_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get spaced repetition statistics."""
        queryset = SpacedRepetitionCardModel.objects.filter(user_id=user_id)
        
        if facet_id:
            queryset = queryset.filter(question__facet_id=facet_id)

        stats = await queryset.aggregate(
            total_cards=Count('id'),
            new_cards=Count('id', filter=Q(state='new')),
            learning_cards=Count('id', filter=Q(state='learning')),
            review_cards=Count('id', filter=Q(state='review')),
            suspended_cards=Count('id', filter=Q(state='suspended')),
            average_ease=Avg('ease_factor'),
            average_interval=Avg('interval_days'),
            total_reviews=Sum('total_reviews'),
            total_correct=Sum('total_correct'),
            average_lapses=Avg('lapses')
        )

        # Calculate success rate
        total_reviews = stats['total_reviews'] or 0
        total_correct = stats['total_correct'] or 0
        success_rate = (total_correct / total_reviews * 100) if total_reviews > 0 else 0

        return {
            'total_cards': stats['total_cards'] or 0,
            'new_cards': stats['new_cards'] or 0,
            'learning_cards': stats['learning_cards'] or 0,
            'review_cards': stats['review_cards'] or 0,
            'suspended_cards': stats['suspended_cards'] or 0,
            'average_ease_factor': stats['average_ease'] or 2.5,
            'average_interval_days': stats['average_interval'] or 0,
            'total_reviews': total_reviews,
            'success_rate': success_rate,
            'average_lapses': stats['average_lapses'] or 0
        }

    async def count_reviews_today(self, user_id: UUID) -> int:
        """Count cards reviewed today."""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        return await SpacedRepetitionCardModel.objects.filter(
            user_id=user_id,
            last_reviewed_at__gte=today_start
        ).acount()

    def _to_entity(self, model: SpacedRepetitionCardModel) -> SpacedRepetitionCard:
        """Convert model to entity."""
        # Create statistics
        statistics = CardStatistics(
            total_reviews=model.total_reviews,
            total_correct=model.total_correct,
            total_time_seconds=model.total_time_seconds,
            lapses=model.lapses,
            last_ease_factor=model.last_ease_factor,
            last_interval_days=model.last_interval_days
        )

        # Parse review config
        review_config = ReviewInterval.default()
        if model.review_config:
            config_data = model.review_config
            review_config = ReviewInterval(
                learning_steps=config_data.get('learning_steps', [1, 10]),
                graduating_interval=config_data.get('graduating_interval', 1),
                easy_interval=config_data.get('easy_interval', 4),
                starting_ease=config_data.get('starting_ease', 2.5),
                easy_bonus=config_data.get('easy_bonus', 1.3),
                interval_modifier=config_data.get('interval_modifier', 1.0),
                maximum_interval=config_data.get('maximum_interval', 36500),
                leech_threshold=config_data.get('leech_threshold', 8)
            )

        return SpacedRepetitionCard(
            id=model.id,
            user_id=model.user_id,
            question_id=model.question_id,
            state=CardState(model.state),
            ease_factor=model.ease_factor,
            interval_days=model.interval_days,
            due_date=model.due_date,
            last_reviewed_at=model.last_reviewed_at,
            statistics=statistics,
            review_config=review_config,
            learning_step=model.learning_step,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def _to_model(self, entity: SpacedRepetitionCard) -> SpacedRepetitionCardModel:
        """Convert entity to model."""
        return SpacedRepetitionCardModel(
            id=entity.id,
            user_id=entity.user_id,
            question_id=entity.question_id,
            state=entity.state.value,
            ease_factor=entity.ease_factor,
            interval_days=entity.interval_days,
            due_date=entity.due_date,
            learning_step=entity.learning_step,
            last_reviewed_at=entity.last_reviewed_at,
            total_reviews=entity.statistics.total_reviews,
            total_correct=entity.statistics.total_correct,
            total_time_seconds=entity.statistics.total_time_seconds,
            lapses=entity.statistics.lapses,
            last_ease_factor=entity.statistics.last_ease_factor,
            last_interval_days=entity.statistics.last_interval_days,
            review_config={
                'learning_steps': entity.review_config.learning_steps,
                'graduating_interval': entity.review_config.graduating_interval,
                'easy_interval': entity.review_config.easy_interval,
                'starting_ease': entity.review_config.starting_ease,
                'easy_bonus': entity.review_config.easy_bonus,
                'interval_modifier': entity.review_config.interval_modifier,
                'maximum_interval': entity.review_config.maximum_interval,
                'leech_threshold': entity.review_config.leech_threshold
            }
        )