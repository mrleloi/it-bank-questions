"""Review card use case."""

from uuid import UUID

from domain.repositories import SpacedRepetitionRepository, ProgressRepository
from domain.services import SpacedRepetitionService
from domain.value_objects import DifficultyRating
from domain.exceptions import EntityNotFoundException, BusinessRuleViolationException
from domain.events import CardReviewedEvent
from application.dto.request import ReviewCardRequest
from application.services import EventBus


class ReviewCardUseCase:
    """Use case for reviewing a spaced repetition card."""

    def __init__(
            self,
            sr_repository: SpacedRepetitionRepository,
            progress_repository: ProgressRepository,
            sr_service: SpacedRepetitionService,
            event_bus: EventBus
    ):
        self.sr_repo = sr_repository
        self.progress_repo = progress_repository
        self.sr_service = sr_service
        self.event_bus = event_bus

    async def execute(self, request: ReviewCardRequest, user_id: UUID) -> dict:
        """Review a spaced repetition card."""
        # Validate request
        request.validate()

        # Get card
        card = await self.sr_repo.get_by_id(request.card_id)
        if not card:
            raise EntityNotFoundException("Card not found")

        # Verify user owns the card
        if card.user_id != user_id:
            raise EntityNotFoundException("Card not found")

        # Check if card can be reviewed
        if not card.can_review():
            raise BusinessRuleViolationException(
                f"Card cannot be reviewed in {card.state.value} state"
            )

        # Convert difficulty rating
        difficulty_rating = DifficultyRating(request.difficulty_rating)

        # Get old state for comparison
        old_state = card.state
        old_due_date = card.due_date
        old_interval = card.interval_days

        # Review the card using domain service
        updated_card = await self.sr_service.review_card(
            card_id=request.card_id,
            rating=difficulty_rating,
            time_seconds=request.time_spent_seconds
        )

        # Update progress based on review
        await self._update_progress(updated_card, difficulty_rating)

        # Publish domain event
        event = CardReviewedEvent(
            card_id=updated_card.id,
            user_id=user_id,
            question_id=updated_card.question_id,
            old_state=old_state.value,
            new_state=updated_card.state.value,
            difficulty_rating=difficulty_rating.value,
            old_interval_days=old_interval,
            new_interval_days=updated_card.interval_days,
            old_due_date=old_due_date,
            new_due_date=updated_card.due_date,
            ease_factor=updated_card.ease_factor,
            review_time_seconds=request.time_spent_seconds
        )
        await self.event_bus.publish(event)

        # Return review result
        return {
            'card_id': str(updated_card.id),
            'new_state': updated_card.state.value,
            'new_interval_days': updated_card.interval_days,
            'next_review_date': updated_card.due_date.isoformat(),
            'ease_factor': updated_card.ease_factor,
            'total_reviews': updated_card.statistics.total_reviews,
            'accuracy_rate': updated_card.statistics.accuracy_rate,
            'is_leech': updated_card.statistics.is_leech()
        }

    async def _update_progress(self, card, difficulty_rating: DifficultyRating):
        """Update progress based on card review."""
        try:
            # Determine if review was successful
            is_correct = difficulty_rating != DifficultyRating.VERY_HARD

            # Get question to determine facet
            from domain.repositories import QuestionRepository
            # This would need to be injected in real implementation
            # For now, we'll assume we can get facet_id from card somehow
            
            # Update user progress
            user_progress = await self.progress_repo.get_user_progress(card.user_id)
            if user_progress:
                user_progress.total_questions_answered += 1
                if is_correct:
                    user_progress.total_correct_answers += 1
                
                await self.progress_repo.save(user_progress)

            # Note: In full implementation, we'd also update facet progress
            # This requires knowing the facet_id from the question

        except Exception as e:
            # Log error but don't fail the review
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to update progress for card review {card.id}: {e}")

    async def bulk_review_cards(
            self,
            reviews: list[ReviewCardRequest],
            user_id: UUID
    ) -> list[dict]:
        """Review multiple cards in batch."""
        results = []
        
        for review in reviews:
            try:
                result = await self.execute(review, user_id)
                results.append(result)
            except Exception as e:
                results.append({
                    'card_id': str(review.card_id),
                    'error': str(e),
                    'success': False
                })
        
        return results