"""Session-related response DTOs."""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID


@dataclass
class SessionMetricsResponse:
    """Session metrics response."""

    total_questions: int
    answered_questions: int
    correct_answers: int
    accuracy_rate: float
    average_time_per_question: float
    total_time_seconds: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'total_questions': self.total_questions,
            'answered_questions': self.answered_questions,
            'correct_answers': self.correct_answers,
            'accuracy_rate': self.accuracy_rate,
            'average_time_per_question': self.average_time_per_question,
            'total_time_seconds': self.total_time_seconds
        }


@dataclass
class SessionResponse:
    """Learning session response."""

    id: UUID
    status: str
    started_at: datetime
    ended_at: Optional[datetime]
    facet_id: Optional[UUID]
    metrics: SessionMetricsResponse

    # Queue info
    questions_remaining: int
    current_question_id: Optional[UUID]

    # Limits
    question_limit: Optional[int]
    time_limit_minutes: Optional[int]
    time_remaining_seconds: Optional[int]

    @classmethod
    def from_entity(cls, session: 'LearningSession') -> 'SessionResponse':
        """Create from LearningSession entity."""
        metrics = SessionMetricsResponse(
            total_questions=session.metrics.total_questions,
            answered_questions=session.metrics.answered_questions,
            correct_answers=session.metrics.correct_answers,
            accuracy_rate=session.metrics.accuracy_rate,
            average_time_per_question=session.metrics.average_time_per_question,
            total_time_seconds=session.metrics.total_time_seconds
        )

        time_remaining = None
        if session.time_limit_minutes:
            elapsed = (datetime.now() - session.started_at).total_seconds()
            time_remaining = max(0, session.time_limit_minutes * 60 - elapsed)

        return cls(
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
            time_remaining_seconds=time_remaining
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': str(self.id),
            'status': self.status,
            'started_at': self.started_at.isoformat(),
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'facet_id': str(self.facet_id) if self.facet_id else None,
            'metrics': self.metrics.to_dict(),
            'queue': {
                'remaining': self.questions_remaining,
                'current_question_id': str(self.current_question_id) if self.current_question_id else None
            },
            'limits': {
                'question_limit': self.question_limit,
                'time_limit_minutes': self.time_limit_minutes,
                'time_remaining_seconds': self.time_remaining_seconds
            }
        }