"""Learning-related request DTOs."""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime


@dataclass
class StartSessionRequest:
    """Start learning session request."""

    facet_id: Optional[UUID] = None
    question_limit: Optional[int] = None
    time_limit_minutes: Optional[int] = None
    question_types: List[str] = field(default_factory=list)
    difficulty_min: int = 1
    difficulty_max: int = 5

    def validate(self) -> None:
        """Validate session parameters."""
        if self.question_limit is not None and self.question_limit <= 0:
            raise ValueError("Question limit must be positive")

        if self.time_limit_minutes is not None and self.time_limit_minutes <= 0:
            raise ValueError("Time limit must be positive")

        if self.difficulty_min < 1 or self.difficulty_min > 5:
            raise ValueError("Minimum difficulty must be between 1 and 5")

        if self.difficulty_max < 1 or self.difficulty_max > 5:
            raise ValueError("Maximum difficulty must be between 1 and 5")

        if self.difficulty_min > self.difficulty_max:
            raise ValueError("Minimum difficulty cannot exceed maximum")

        valid_types = ['mcq', 'theory', 'scenario']
        for qt in self.question_types:
            if qt not in valid_types:
                raise ValueError(f"Invalid question type: {qt}")


@dataclass
class GetNextQuestionRequest:
    """Get next question request."""

    user_id: UUID
    session_id: UUID
    facet_id: Optional[UUID] = None
    prefer_review: bool = True  # Prefer review cards over new

    def validate(self) -> None:
        """Validate request."""
        if not self.user_id:
            raise ValueError("User ID is required")

        if not self.session_id:
            raise ValueError("Session ID is required")


@dataclass
class SubmitAnswerRequest:
    """Submit answer request."""

    question_id: UUID
    session_id: UUID
    answer: Optional[str] = None  # For MCQ: option key, for others: text
    time_spent_seconds: int = 0
    confidence_level: int = 3  # 1-5 scale
    difficulty_rating: int = 2  # 1-4: Easy, Medium, Hard, Very Hard

    def validate(self) -> None:
        """Validate answer submission."""
        if not self.question_id:
            raise ValueError("Question ID is required")

        if not self.session_id:
            raise ValueError("Session ID is required")

        if self.time_spent_seconds < 0:
            raise ValueError("Time spent cannot be negative")

        if self.confidence_level < 1 or self.confidence_level > 5:
            raise ValueError("Confidence level must be between 1 and 5")

        if self.difficulty_rating < 1 or self.difficulty_rating > 4:
            raise ValueError("Difficulty rating must be between 1 and 4")


@dataclass
class ReviewCardRequest:
    """Review spaced repetition card request."""

    card_id: UUID
    difficulty_rating: int  # 1-4: Easy, Medium, Hard, Very Hard
    time_spent_seconds: int

    def validate(self) -> None:
        """Validate review."""
        if not self.card_id:
            raise ValueError("Card ID is required")

        if self.difficulty_rating < 1 or self.difficulty_rating > 4:
            raise ValueError("Difficulty rating must be between 1 and 4")

        if self.time_spent_seconds < 0:
            raise ValueError("Time spent cannot be negative")


@dataclass
class GetLearningPathRequest:
    """Get learning path request."""

    user_id: UUID
    current_facet_id: Optional[UUID] = None
    include_recommendations: bool = True

    def validate(self) -> None:
        """Validate request."""
        if not self.user_id:
            raise ValueError("User ID is required")


@dataclass
class RequestHintRequest:
    """Request hint for question."""

    question_id: UUID
    session_id: UUID
    hint_level: int = 1  # 1: subtle, 2: moderate, 3: explicit

    def validate(self) -> None:
        """Validate hint request."""
        if not self.question_id:
            raise ValueError("Question ID is required")

        if not self.session_id:
            raise ValueError("Session ID is required")

        if self.hint_level < 1 or self.hint_level > 3:
            raise ValueError("Hint level must be between 1 and 3")
