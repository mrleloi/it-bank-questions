"""Request hint use case."""

from uuid import UUID

from domain.repositories import QuestionRepository, SessionRepository, EventRepository
from domain.entities import LearningEvent
from domain.entities.learning_event import EventType
from domain.exceptions import EntityNotFoundException, BusinessRuleViolationException
from application.dto.request import RequestHintRequest
from application.dto.response import HintResponse


class RequestHintUseCase:
    """Use case for requesting hints for questions."""

    def __init__(
            self,
            question_repository: QuestionRepository,
            session_repository: SessionRepository,
            event_repository: EventRepository
    ):
        self.question_repo = question_repository
        self.session_repo = session_repository
        self.event_repo = event_repository

    async def execute(self, request: RequestHintRequest, user_id: UUID) -> HintResponse:
        """Request a hint for a question."""
        # Validate request
        request.validate()

        # Get session and verify ownership
        session = await self.session_repo.get_by_id(request.session_id)
        if not session or session.user_id != user_id:
            raise EntityNotFoundException("Session not found")

        # Check if session is active
        if not session.is_active():
            raise BusinessRuleViolationException("Session is not active")

        # Get question
        question = await self.question_repo.get_by_id(request.question_id)
        if not question:
            raise EntityNotFoundException("Question not found")

        # Check if question is part of current session
        if (session.current_question_id != request.question_id and 
            request.question_id not in session.answered_questions and
            request.question_id not in session.question_queue):
            raise BusinessRuleViolationException("Question is not part of current session")

        # Get available hints
        available_hints = question.metadata.hints
        if not available_hints:
            raise BusinessRuleViolationException("No hints available for this question")

        # Count hints already used for this question in this session
        hints_used = await self._count_hints_used(
            user_id, request.question_id, request.session_id
        )

        # Check if hint level is valid
        if request.hint_level <= hints_used:
            raise BusinessRuleViolationException("This hint level already used")

        if request.hint_level > len(available_hints):
            raise BusinessRuleViolationException("Hint level not available")

        # Get the requested hint (hints are 0-indexed, request is 1-indexed)
        hint_index = request.hint_level - 1
        hint_text = available_hints[hint_index]

        # Calculate remaining hints
        hints_remaining = len(available_hints) - request.hint_level

        # Record hint usage
        await self._record_hint_usage(
            user_id=user_id,
            question_id=request.question_id,
            session_id=request.session_id,
            hint_level=request.hint_level,
            hint_text=hint_text
        )

        # Return hint response
        return HintResponse(
            hint_text=hint_text,
            hint_level=request.hint_level,
            hints_remaining=hints_remaining
        )

    async def _count_hints_used(
            self, 
            user_id: UUID, 
            question_id: UUID, 
            session_id: UUID
    ) -> int:
        """Count hints already used for this question in this session."""
        hint_events = await self.event_repo.get_session_events(
            session_id=session_id,
            event_types=[EventType.HINT_REQUESTED]
        )
        
        # Count hints for this specific question
        question_hints = [
            event for event in hint_events 
            if event.question_id == question_id and event.user_id == user_id
        ]
        
        return len(question_hints)

    async def _record_hint_usage(
            self,
            user_id: UUID,
            question_id: UUID,
            session_id: UUID,
            hint_level: int,
            hint_text: str
    ) -> None:
        """Record hint usage as learning event."""
        event = LearningEvent(
            user_id=user_id,
            event_type=EventType.HINT_REQUESTED,
            event_data={
                'question_id': str(question_id),
                'session_id': str(session_id),
                'hint_level': hint_level,
                'hint_text': hint_text[:100]  # Truncate for privacy/storage
            },
            session_id=session_id,
            question_id=question_id
        )
        
        await self.event_repo.save(event)

    async def get_available_hints(
            self, 
            question_id: UUID, 
            user_id: UUID,
            session_id: UUID
    ) -> dict:
        """Get information about available hints for a question."""
        # Get question
        question = await self.question_repo.get_by_id(question_id)
        if not question:
            raise EntityNotFoundException("Question not found")

        # Get session
        session = await self.session_repo.get_by_id(session_id)
        if not session or session.user_id != user_id:
            raise EntityNotFoundException("Session not found")

        # Count hints used
        hints_used = await self._count_hints_used(user_id, question_id, session_id)
        
        available_hints = question.metadata.hints
        total_hints = len(available_hints)
        
        return {
            'total_hints': total_hints,
            'hints_used': hints_used,
            'hints_remaining': max(0, total_hints - hints_used),
            'next_hint_level': hints_used + 1 if hints_used < total_hints else None,
            'has_hints': total_hints > 0
        }