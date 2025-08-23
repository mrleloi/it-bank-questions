"""Get next question use case."""

from typing import Optional
from uuid import UUID

from domain.repositories import (
    SessionRepository,
    QuestionRepository,
    SpacedRepetitionRepository
)
from domain.services import SpacedRepetitionService
from domain.exceptions import EntityNotFoundException, SessionExpiredException
from application.dto.request import GetNextQuestionRequest
from application.dto.response import QuestionResponse
from application.mappers import QuestionMapper


class GetNextQuestionUseCase:
    """Use case for getting next question."""

    def __init__(
            self,
            session_repository: SessionRepository,
            question_repository: QuestionRepository,
            sr_repository: SpacedRepetitionRepository,
            sr_service: SpacedRepetitionService
    ):
        self.session_repo = session_repository
        self.question_repo = question_repository
        self.sr_repo = sr_repository
        self.sr_service = sr_service

    async def execute(self, request: GetNextQuestionRequest) -> Optional[QuestionResponse]:
        """Get next question for the session."""
        # Validate request
        request.validate()

        # Get session
        session = await self.session_repo.get_by_id(request.session_id)
        if not session:
            raise EntityNotFoundException("Session not found")

        if session.user_id != request.user_id:
            raise EntityNotFoundException("Session not found")

        if session.is_expired():
            raise SessionExpiredException("Session has expired")

        # Check if should complete session
        if session.should_complete():
            session.complete()
            await self.session_repo.save(session)
            return None

        question = None
        card = None

        # Try to get from session queue first
        if session.question_queue:
            question_id = session.question_queue[0]
            question = await self.question_repo.get_by_id(question_id)

            # Get card if exists
            card = await self.sr_repo.get_by_user_and_question(
                request.user_id, question_id
            )

        # If no questions in queue, get from spaced repetition
        elif request.facet_id and request.prefer_review:
            card = await self.sr_service.get_next_card(
                user_id=request.user_id,
                facet_id=request.facet_id
            )

            if card:
                question = await self.question_repo.get_by_id(card.question_id)
                session.add_questions([question.id])
                await self.session_repo.save(session)

        # Get new questions if no reviews
        if not question and request.facet_id:
            new_questions = await self.question_repo.get_unanswered_by_user(
                user_id=request.user_id,
                facet_id=request.facet_id,
                limit=1
            )

            if new_questions:
                question = new_questions[0]
                session.add_questions([question.id])
                await self.session_repo.save(session)

        if not question:
            return None

        # Start question in session
        session.start_question(question.id)
        await self.session_repo.save(session)

        return QuestionMapper.to_response_dto(question, card)
