"""Learning session entity."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from uuid import UUID
from enum import Enum

from ..exceptions import (
    EntityValidationException,
    InvalidStateTransitionException,
    SessionExpiredException
)
from .base import Entity


class SessionStatus(str, Enum):
    """Learning session status."""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"

    def can_answer(self) -> bool:
        """Check if can answer questions in this status."""
        return self == SessionStatus.ACTIVE


@dataclass
class SessionMetrics:
    """Metrics for a learning session."""

    total_questions: int = 0
    answered_questions: int = 0
    correct_answers: int = 0
    total_time_seconds: int = 0
    active_time_seconds: int = 0
    average_time_per_question: float = 0.0
    accuracy_rate: float = 0.0

    def update(self, is_correct: bool, time_seconds: int) -> None:
        """Update metrics after answering a question."""
        self.answered_questions += 1
        if is_correct:
            self.correct_answers += 1
        self.active_time_seconds += time_seconds

        # Update averages
        if self.answered_questions > 0:
            self.average_time_per_question = self.active_time_seconds / self.answered_questions
            self.accuracy_rate = (self.correct_answers / self.answered_questions) * 100.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'total_questions': self.total_questions,
            'answered_questions': self.answered_questions,
            'correct_answers': self.correct_answers,
            'total_time_seconds': self.total_time_seconds,
            'active_time_seconds': self.active_time_seconds,
            'average_time_per_question': self.average_time_per_question,
            'accuracy_rate': self.accuracy_rate,
        }


@dataclass
class LearningSession(Entity):
    """Learning session entity."""

    user_id: UUID
    facet_id: Optional[UUID] = None
    status: SessionStatus = SessionStatus.ACTIVE
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    last_activity_at: datetime = field(default_factory=datetime.now)
    metrics: SessionMetrics = field(default_factory=SessionMetrics)

    # Session configuration
    question_limit: Optional[int] = None  # Max questions for this session
    time_limit_minutes: Optional[int] = None  # Max time for this session
    question_types: List[str] = field(default_factory=list)  # Filter by question types
    difficulty_range: tuple[int, int] = (1, 5)  # Min and max difficulty

    # Question tracking
    question_queue: List[UUID] = field(default_factory=list)
    answered_questions: List[UUID] = field(default_factory=list)
    current_question_id: Optional[UUID] = None
    current_question_started_at: Optional[datetime] = None

    def validate(self) -> None:
        """Validate session entity."""
        if self.question_limit is not None and self.question_limit <= 0:
            raise EntityValidationException("Question limit must be positive")

        if self.time_limit_minutes is not None and self.time_limit_minutes <= 0:
            raise EntityValidationException("Time limit must be positive")

        if self.difficulty_range[0] > self.difficulty_range[1]:
            raise EntityValidationException("Invalid difficulty range")

    def is_active(self) -> bool:
        """Check if session is active."""
        return self.status == SessionStatus.ACTIVE

    def is_expired(self) -> bool:
        """Check if session has expired due to inactivity."""
        if self.status != SessionStatus.ACTIVE:
            return False

        # Session expires after 30 minutes of inactivity
        expiry_time = self.last_activity_at + timedelta(minutes=30)
        return datetime.now() > expiry_time

    def has_time_limit_exceeded(self) -> bool:
        """Check if time limit has been exceeded."""
        if self.time_limit_minutes is None:
            return False

        elapsed_minutes = (datetime.now() - self.started_at).total_seconds() / 60
        return elapsed_minutes > self.time_limit_minutes

    def has_question_limit_reached(self) -> bool:
        """Check if question limit has been reached."""
        if self.question_limit is None:
            return False

        return len(self.answered_questions) >= self.question_limit

    def should_complete(self) -> bool:
        """Check if session should be completed."""
        return (
                self.has_time_limit_exceeded() or
                self.has_question_limit_reached() or
                (len(self.question_queue) == 0 and self.current_question_id is None)
        )

    def start_question(self, question_id: UUID) -> None:
        """Start answering a question."""
        if not self.is_active():
            raise InvalidStateTransitionException(f"Cannot start question in {self.status} session")

        if self.is_expired():
            raise SessionExpiredException("Session has expired due to inactivity")

        if self.current_question_id is not None:
            raise EntityValidationException("Already answering a question")

        self.current_question_id = question_id
        self.current_question_started_at = datetime.now()
        self.last_activity_at = datetime.now()
        self.update_timestamp()

    def resume(self) -> None:
        """Resume a paused session."""
        if self.status != SessionStatus.PAUSED:
            raise InvalidStateTransitionException(f"Cannot resume {self.status} session")

        self.status = SessionStatus.ACTIVE
        self.last_activity_at = datetime.now()
        self.update_timestamp()

    def complete(self) -> None:
        """Complete the session."""
        if self.status in {SessionStatus.COMPLETED, SessionStatus.ABANDONED}:
            raise InvalidStateTransitionException(f"Session already {self.status}")

        self.status = SessionStatus.COMPLETED
        self.ended_at = datetime.now()
        self.metrics.total_time_seconds = int((self.ended_at - self.started_at).total_seconds())
        self.update_timestamp()

    def abandon(self) -> None:
        """Abandon the session."""
        if self.status in {SessionStatus.COMPLETED, SessionStatus.ABANDONED}:
            raise InvalidStateTransitionException(f"Session already {self.status}")

        self.status = SessionStatus.ABANDONED
        self.ended_at = datetime.now()
        self.metrics.total_time_seconds = int((self.ended_at - self.started_at).total_seconds())
        self.update_timestamp()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = super().to_dict()
        data.update({
            'user_id': str(self.user_id),
            'facet_id': str(self.facet_id) if self.facet_id else None,
            'status': self.status.value,
            'started_at': self.started_at.isoformat(),
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'last_activity_at': self.last_activity_at.isoformat(),
            'metrics': self.metrics.to_dict(),
            'question_limit': self.question_limit,
            'time_limit_minutes': self.time_limit_minutes,
            'question_types': self.question_types,
            'difficulty_range': list(self.difficulty_range),
            'question_queue': [str(qid) for qid in self.question_queue],
            'answered_questions': [str(qid) for qid in self.answered_questions],
            'current_question_id': str(self.current_question_id) if self.current_question_id else None,
            'is_expired': self.is_expired(),
            'should_complete': self.should_complete(),
        })
        return data()

    def answer_question(self, is_correct: bool) -> int:
        """
        Complete answering current question.

        Returns:
            Time taken in seconds
        """
        if not self.is_active():
            raise InvalidStateTransitionException(f"Cannot answer question in {self.status} session")

        if self.current_question_id is None:
            raise EntityValidationException("No question is being answered")

        # Calculate time taken
        time_taken = int((datetime.now() - self.current_question_started_at).total_seconds())

        # Update metrics
        self.metrics.update(is_correct, time_taken)

        # Move question to answered
        self.answered_questions.append(self.current_question_id)
        if self.current_question_id in self.question_queue:
            self.question_queue.remove(self.current_question_id)

        # Reset current question
        self.current_question_id = None
        self.current_question_started_at = None
        self.last_activity_at = datetime.now()
        self.update_timestamp()

        # Check if should complete
        if self.should_complete():
            self.complete()

        return time_taken

    def add_questions(self, question_ids: List[UUID]) -> None:
        """Add questions to the queue."""
        if not self.is_active():
            raise InvalidStateTransitionException(f"Cannot add questions to {self.status} session")

        for qid in question_ids:
            if qid not in self.question_queue and qid not in self.answered_questions:
                self.question_queue.append(qid)

        self.metrics.total_questions = len(self.question_queue) + len(self.answered_questions)
        self.update_timestamp()

    def pause(self) -> None:
        """Pause the session."""
        if self.status != SessionStatus.ACTIVE:
            raise InvalidStateTransitionException(f"Cannot pause {self.status} session")

        self.status = SessionStatus.PAUSED
        self.last_activity_at = datetime.now()
        self.update_timestamp  # Domain Layer Implementation
