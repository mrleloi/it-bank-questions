"""Session mapper."""

from typing import Optional
from uuid import UUID
from datetime import datetime

from domain.entities import LearningSession
from application.dto.response import SessionResponse, SessionMetricsResponse
from application.dto.request import StartSessionRequest


class SessionMapper:
    """Mapper for LearningSession entity and DTOs."""

    @staticmethod
    def to_response_dto(session: LearningSession) -> SessionResponse:
        """Convert LearningSession entity to response DTO."""
        metrics = SessionMetricsResponse(
            total_questions=session.metrics.total_questions,
            answered_questions=session.metrics.answered_questions,
            correct_answers=session.metrics.correct_answers,
            accuracy_rate=session.metrics.accuracy_rate,
            average_time_per_question=session.metrics.average_time_per_question,
            total_time_seconds=session.metrics.total_time_seconds
        )

        # Calculate time remaining if there's a time limit
        time_remaining = None
        if session.time_limit_minutes:
            elapsed = (datetime.now() - session.started_at).total_seconds()
            time_remaining = max(0, session.time_limit_minutes * 60 - elapsed)

        return SessionResponse(
            id=session.id,
            status=session.status.value,
            started_at=session.started_at,
            ended_at=session.ended_at,
            facet_id=session.facet_id,
            metrics=metrics,
            questions_remaining=len(session.question_queue),
            current_question_id=session.current_question_id,
            question_limit=session.question_limit,
            time_limit_minutes=session.time_limit_minutes,
            time_remaining_seconds=int(time_remaining) if time_remaining else None
        )

    @staticmethod
    def from_start_request(request: StartSessionRequest, user_id: UUID) -> LearningSession:
        """Create LearningSession entity from start request."""
        session = LearningSession(
            user_id=user_id,
            facet_id=request.facet_id,
            question_limit=request.question_limit,
            time_limit_minutes=request.time_limit_minutes,
            question_types=request.question_types,
            difficulty_range=(request.difficulty_min, request.difficulty_max)
        )

        return session