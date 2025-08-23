"""Spaced repetition domain service."""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta

from ..entities import SpacedRepetitionCard, Question
from ..value_objects import DifficultyRating, CardState, ReviewInterval
from ..repositories import SpacedRepetitionRepository, QuestionRepository
from ..exceptions import EntityNotFoundException, BusinessRuleViolationException


class SpacedRepetitionService:
    """Service for spaced repetition logic."""

    def __init__(
            self,
            card_repository: SpacedRepetitionRepository,
            question_repository: QuestionRepository
    ):
        self.card_repo = card_repository
        self.question_repo = question_repository

    async def get_next_card(
            self,
            user_id: UUID,
            facet_id: Optional[UUID] = None,
            daily_limit: int = 20
    ) -> Optional[SpacedRepetitionCard]:
        """
        Get next card for review based on priority:
        1. Overdue cards
        2. Learning cards due now
        3. New cards (up to daily limit)
        4. Review cards due today
        """
        # Check overdue cards first (highest priority)
        overdue = await self.card_repo.get_overdue_cards(
            user_id, facet_id, limit=1
        )
        if overdue:
            return overdue[0]

        # Check learning cards
        learning = await self.card_repo.get_learning_cards(
            user_id, facet_id, limit=1
        )
        if learning and learning[0].can_review():
            return learning[0]

        # Check new card limit
        today_new_count = await self._get_today_new_count(user_id, facet_id)
        if today_new_count < daily_limit:
            new_cards = await self.card_repo.get_new_cards(
                user_id, facet_id, limit=1
            )
            if new_cards:
                return new_cards[0]

        # Finally, check regular review cards
        due = await self.card_repo.get_due_cards(
            user_id, facet_id, limit=1
        )
        if due:
            return due[0]

        return None

    async def review_card(
            self,
            card_id: UUID,
            rating: DifficultyRating,
            time_seconds: int
    ) -> SpacedRepetitionCard:
        """Process a card review."""
        card = await self.card_repo.get_by_id(card_id)
        if not card:
            raise EntityNotFoundException(f"Card {card_id} not found")

        if not card.can_review():
            raise BusinessRuleViolationException(
                f"Card {card_id} cannot be reviewed in state {card.state}"
            )

        # Process the review
        card.review(rating, time_seconds)

        # Save updated card
        updated_card = await self.card_repo.save(card)

        return updated_card

    async def create_cards_for_user(
            self,
            user_id: UUID,
            facet_id: UUID,
            config: Optional[ReviewInterval] = None
    ) -> List[SpacedRepetitionCard]:
        """Create spaced repetition cards for all questions in a facet."""
        # Get all questions in facet
        questions = await self.question_repo.get_by_facet(facet_id)

        if not questions:
            return []

        # Check existing cards
        existing_cards = []
        for question in questions:
            card = await self.card_repo.get_by_user_and_question(
                user_id, question.id
            )
            if card:
                existing_cards.append(card)

        # Create new cards for questions without cards
        new_cards = []
        for question in questions:
            if not any(c.question_id == question.id for c in existing_cards):
                card = SpacedRepetitionCard(
                    user_id=user_id,
                    question_id=question.id,
                    review_config=config or ReviewInterval.default()
                )
                new_cards.append(card)

        # Bulk save new cards
        if new_cards:
            saved_cards = []
            for card in new_cards:
                saved = await self.card_repo.save(card)
                saved_cards.append(saved)
            return saved_cards

        return existing_cards

    async def get_review_forecast(
            self,
            user_id: UUID,
            facet_id: Optional[UUID] = None,
            days: int = 30
    ) -> Dict[str, Any]:
        """Get forecast of reviews for next N days."""
        forecast = {}
        today = datetime.now().date()

        for i in range(days):
            date = today + timedelta(days=i)

            # Get cards due on this date
            start = datetime.combine(date, datetime.min.time())
            end = datetime.combine(date, datetime.max.time())

            due_cards = await self.card_repo.get_due_cards(
                user_id, facet_id
            )

            # Count cards due on this specific date
            count = sum(
                1 for card in due_cards
                if start <= card.due_date <= end
            )

            forecast[date.isoformat()] = count

        return {
            'forecast': forecast,
            'total_reviews': sum(forecast.values()),
            'average_per_day': sum(forecast.values()) / days
        }

    async def optimize_review_schedule(
            self,
            user_id: UUID,
            facet_id: UUID,
            target_mastery_days: int = 30
    ) -> ReviewInterval:
        """
        Optimize review interval configuration based on user's performance.
        """
        stats = await self.card_repo.get_statistics(user_id, facet_id)

        # Analyze user's performance
        avg_ease = stats.get('average_ease_factor', 2.5)
        success_rate = stats.get('success_rate', 0.7)
        avg_lapses = stats.get('average_lapses', 2)

        # Adjust intervals based on performance
        if success_rate > 0.85 and avg_ease > 2.7:
            # User is doing well, can use more relaxed intervals
            return ReviewInterval.relaxed()
        elif success_rate < 0.6 or avg_lapses > 5:
            # User is struggling, use more aggressive intervals
            return ReviewInterval.aggressive()
        else:
            # Default intervals with slight adjustments
            config = ReviewInterval.default()
            config.interval_modifier = 0.9 if success_rate < 0.7 else 1.1
            return config

    async def _get_today_new_count(
            self,
            user_id: UUID,
            facet_id: Optional[UUID]
    ) -> int:
        """Get count of new cards reviewed today."""
        today_start = datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        # Get cards reviewed today that were new
        all_cards = await self.card_repo.get_cards_by_state(
            user_id, CardState.LEARNING, facet_id
        )

        today_new = sum(
            1 for card in all_cards
            if card.last_reviewed_at and card.last_reviewed_at >= today_start
            and card.statistics.total_reviews == 1
        )

        return today_new