"""Start learning session use case."""

from typing import Optional
from uuid import UUID

from domain.entities import LearningSession
from domain.repositories import SessionRepository, QuestionRepository
from domain.events import SessionStartedEvent
from domain.services import LearningPathService
from application.dto.request import StartSessionRequest
from application.dto.response import SessionResponse
from application.mappers import SessionMapper
from application.services import EventBus


class StartLearningSessionUseCase:
    """Use case for starting a learning session."""

    def __init__(
            self,
            session_repository: SessionRepository,
            question_repository: QuestionRepository,
            learning_path_service: LearningPathService,
            event_bus: EventBus
    ):
        self.session_repo = session_repository
        self.question_repo = question_repository
        self.learning_path = learning_path_service
        self.event_bus = event_bus

    async def execute(
            self,
            request: StartSessionRequest,
            user_id: UUID
    ) -> SessionResponse:
        """Start a new learning session."""
        # Validate request
        request.validate()

        # Check for existing active session
        active_session = await self.session_repo.get_active_session(user_id)
        if active_session:
            # Complete or return existing session
            if active_session.is_expired():
                active_session.abandon()
                await self.session_repo.save(active_session)
            else:
                return SessionMapper.to_response_dto(active_session)

        # Create new session
        session = LearningSession(
            user_id=user_id,
            facet_id=request.facet_id,
            question_limit=request.question_limit,
            time_limit_minutes=request.time_limit_minutes,
            question_types=request.question_types,
            difficulty_range=(request.difficulty_min, request.difficulty_max)
        )

        # Get initial questions
        if request.facet_id:
            questions = await self.learning_path.get_adaptive_questions(
                user_id=user_id,
                facet_id=request.facet_id,
                session=session,
                count=min(request.question_limit or 20, 20)
            )

            session.add_questions([q.id for q in questions])

        # Save session
        saved_session = await self.session_repo.save(session)

        # Publish event
        event = SessionStartedEvent(
            session_id=saved_session.id,
            user_id=user_id,
            facet_id=request.facet_id
        )
        await self.event_bus.publish(event)

        return SessionMapper.to_response_dto(saved_session)