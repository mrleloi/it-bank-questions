"""Submit answer use case."""

from typing import Optional
from uuid import UUID
from datetime import datetime

from domain.entities import SpacedRepetitionCard, LearningEvent
from domain.entities.learning_event import EventType
from domain.repositories import (
    SessionRepository,
    QuestionRepository,
    SpacedRepetitionRepository,
    ProgressRepository,
    EventRepository
)
from domain.services import SpacedRepetitionService, AchievementService
from domain.value_objects import DifficultyRating
from domain.exceptions import EntityNotFoundException, BusinessRuleViolationException
from domain.events import QuestionAnsweredEvent
from application.dto.request import SubmitAnswerRequest
from application.dto.response import AnswerFeedbackResponse
from application.services import EventBus


class SubmitAnswerUseCase:
    """Use case for submitting an answer."""

    def __init__(
            self,
            session_repository: SessionRepository,
            question_repository: QuestionRepository,
            sr_repository: SpacedRepetitionRepository,
            progress_repository: ProgressRepository,
            event_repository: EventRepository,
            sr_service: SpacedRepetitionService,
            achievement_service: AchievementService,
            event_bus: EventBus
    ):
        self.session_repo = session_repository
        self.question_repo = question_repository
        self.sr_repo = sr_repository
        self.progress_repo = progress_repository
        self.event_repo = event_repository
        self.sr_service = sr_service
        self.achievement_service = achievement_service
        self.event_bus = event_bus

    async def execute(
            self,
            request: SubmitAnswerRequest,
            user_id: UUID
    ) -> AnswerFeedbackResponse:
        """Submit an answer for a question."""
        # Validate request
        request.validate()

        # Get session
        session = await self.session_repo.get_by_id(request.session_id)
        if not session or session.user_id != user_id:
            raise EntityNotFoundException("Session not found")

        if not session.is_active():
            raise BusinessRuleViolationException("Session is not active")

        # Get question
        question = await self.question_repo.get_by_id(request.question_id)
        if not question:
            raise EntityNotFoundException("Question not found")

        # Check answer
        is_correct = False
        correct_answer = None
        explanation = None

        if question.is_mcq():
            is_correct = question.check_answer(request.answer)
            correct_answer = question.get_correct_answer()
            explanation = question.get_explanation()
        else:
            # For non-MCQ, we'll need AI evaluation in Phase 2
            # For now, just record the answer
            is_correct = None

        # Complete question in session
        time_taken = session.answer_question(is_correct if is_correct is not None else False)
        await self.session_repo.save(session)

        # Get or create spaced repetition card
        card = await self.sr_repo.get_by_user_and_question(
            user_id, request.question_id
        )

        if not card:
            card = SpacedRepetitionCard(
                user_id=user_id,
                question_id=request.question_id
            )
            card = await self.sr_repo.save(card)

        # Process spaced repetition review
        difficulty_rating = DifficultyRating(request.difficulty_rating)
        card.review(difficulty_rating, request.time_spent_seconds)
        card = await self.sr_repo.save(card)

        # Update progress
        progress = await self.progress_repo.get_facet_progress(
            user_id, question.facet_id
        )

        if progress:
            progress.update_performance(
                correct=is_correct if is_correct is not None else False,
                response_time=float(time_taken),
                difficulty=question.difficulty_level.value
            )
            progress.update_streak(studied_today=True)
            progress = await self.progress_repo.save(progress)

        # Create learning event
        learning_event = LearningEvent(
            user_id=user_id,
            event_type=EventType.QUESTION_ANSWERED,
            event_data={
                'question_id': str(request.question_id),
                'session_id': str(request.session_id),
                'is_correct': is_correct,
                'time_seconds': time_taken,
                'difficulty_rating': request.difficulty_rating,
                'confidence_level': request.confidence_level
            },
            session_id=request.session_id,
            question_id=request.question_id,
            facet_id=question.facet_id
        )
        await self.event_repo.save(learning_event)

        # Check achievements
        new_achievements = await self.achievement_service.check_achievements(
            user_id, learning_event
        )

        # Publish domain event
        event = QuestionAnsweredEvent(
            user_id=user_id,
            question_id=request.question_id,
            session_id=request.session_id,
            is_correct=is_correct if is_correct is not None else False,
            time_taken_seconds=time_taken
        )
        await self.event_bus.publish(event)

        # Build response
        return AnswerFeedbackResponse(
            is_correct=is_correct if is_correct is not None else False,
            correct_answer=correct_answer,
            explanation=explanation,
            time_taken_seconds=time_taken,
            next_review_date=card.due_date,
            new_interval_days=card.interval_days,
            questions_answered_today=session.metrics.answered_questions,
            accuracy_rate=session.metrics.accuracy_rate,
            streak_days=progress.current_streak_days if progress else 0,
            new_achievements=[
                {
                    'name': a.name,
                    'display_name': a.display_name,
                    'points': a.points,
                    'icon': a.icon
                }
                for a in new_achievements
            ] if new_achievements else None
        )