"""End session use case."""

from uuid import UUID

from domain.repositories import SessionRepository, ProgressRepository
from domain.exceptions import EntityNotFoundException, BusinessRuleViolationException
from domain.events import SessionCompletedEvent
from application.services import EventBus


class EndSessionUseCase:
    """Use case for ending a learning session."""

    def __init__(
            self,
            session_repository: SessionRepository,
            progress_repository: ProgressRepository,
            event_bus: EventBus
    ):
        self.session_repo = session_repository
        self.progress_repo = progress_repository
        self.event_bus = event_bus

    async def execute(self, session_id: UUID, user_id: UUID) -> None:
        """End a learning session."""
        # Get session
        session = await self.session_repo.get_by_id(session_id)
        if not session:
            raise EntityNotFoundException("Session not found")

        # Verify user owns the session
        if session.user_id != user_id:
            raise EntityNotFoundException("Session not found")

        # Check if session can be completed
        if not session.is_active():
            raise BusinessRuleViolationException(
                f"Cannot end session in {session.status.value} status"
            )

        # Complete the session
        session.complete()

        # Save session
        await self.session_repo.save(session)

        # Update user progress if session has metrics
        if session.metrics.answered_questions > 0:
            await self._update_progress(session)

        # Publish domain event
        event = SessionCompletedEvent(
            session_id=session.id,
            user_id=session.user_id,
            facet_id=session.facet_id,
            questions_answered=session.metrics.answered_questions,
            correct_answers=session.metrics.correct_answers,
            accuracy_rate=session.metrics.accuracy_rate,
            total_time_seconds=session.metrics.total_time_seconds
        )
        await self.event_bus.publish(event)

    async def _update_progress(self, session) -> None:
        """Update user progress based on session results."""
        try:
            # Update overall user progress
            user_progress = await self.progress_repo.get_user_progress(session.user_id)
            
            if user_progress:
                user_progress.total_questions_answered += session.metrics.answered_questions
                user_progress.total_correct_answers += session.metrics.correct_answers
                user_progress.total_study_time_seconds += session.metrics.total_time_seconds
                
                # Recalculate overall mastery
                user_progress.recalculate_overall_mastery()
                
                await self.progress_repo.save(user_progress)

            # Update facet progress if applicable
            if session.facet_id:
                facet_progress = await self.progress_repo.get_facet_progress(
                    session.user_id, session.facet_id
                )
                
                if facet_progress:
                    # Update performance metrics
                    avg_time = session.metrics.average_time_per_question
                    accuracy = session.metrics.accuracy_rate > 0
                    
                    facet_progress.update_performance(
                        correct=accuracy,
                        response_time=avg_time,
                        difficulty=3  # Average difficulty
                    )
                    
                    # Add study time
                    facet_progress.add_study_time(session.metrics.total_time_seconds)
                    
                    # Update streak (studied today)
                    facet_progress.update_streak(studied_today=True)
                    
                    # Recalculate mastery score
                    facet_progress.calculate_mastery_score()
                    
                    await self.progress_repo.save(facet_progress)

        except Exception as e:
            # Log error but don't fail session completion
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to update progress for session {session.id}: {e}")