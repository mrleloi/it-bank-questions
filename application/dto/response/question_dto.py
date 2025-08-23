"""Question-related response DTOs."""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID


@dataclass
class MCQOptionResponse:
    """MCQ option response."""

    key: str
    text: str

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return {
            'key': self.key,
            'text': self.text
        }


@dataclass
class QuestionResponse:
    """Question response DTO."""

    id: UUID
    type: str
    question_text: str
    difficulty_level: int
    estimated_time_seconds: int

    # MCQ specific
    options: Optional[List[MCQOptionResponse]] = None

    # Metadata
    tags: List[str] = None
    hints_available: bool = False

    # Card info (if reviewing)
    card_state: Optional[str] = None
    due_date: Optional[datetime] = None
    ease_factor: Optional[float] = None

    @classmethod
    def from_entity(
            cls,
            question: 'Question',
            card: Optional['SpacedRepetitionCard'] = None
    ) -> 'QuestionResponse':
        """Create from Question entity."""
        options = None
        if question.is_mcq():
            options = [
                MCQOptionResponse(opt.key, opt.text)
                for opt in question.options
            ]

        response = cls(
            id=question.id,
            type=question.type.value,
            question_text=question.question_text,
            difficulty_level=question.difficulty_level.value,
            estimated_time_seconds=question.get_estimated_time(),
            options=options,
            tags=question.metadata.tags,
            hints_available=len(question.metadata.hints) > 0
        )

        if card:
            response.card_state = card.state.value
            response.due_date = card.due_date
            response.ease_factor = card.ease_factor

        return response

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = {
            'id': str(self.id),
            'type': self.type,
            'question_text': self.question_text,
            'difficulty_level': self.difficulty_level,
            'estimated_time_seconds': self.estimated_time_seconds,
            'tags': self.tags,
            'hints_available': self.hints_available
        }

        if self.options:
            data['options'] = [opt.to_dict() for opt in self.options]

        if self.card_state:
            data['card_info'] = {
                'state': self.card_state,
                'due_date': self.due_date.isoformat() if self.due_date else None,
                'ease_factor': self.ease_factor
            }

        return data


@dataclass
class AnswerFeedbackResponse:
    """Answer feedback response."""

    is_correct: bool
    correct_answer: Optional[str]
    explanation: Optional[str]
    time_taken_seconds: int

    # Spaced repetition info
    next_review_date: Optional[datetime] = None
    new_interval_days: Optional[int] = None

    # Progress update
    questions_answered_today: int = 0
    accuracy_rate: float = 0.0
    streak_days: int = 0

    # Achievements
    new_achievements: List[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = {
            'is_correct': self.is_correct,
            'correct_answer': self.correct_answer,
            'explanation': self.explanation,
            'time_taken_seconds': self.time_taken_seconds,
            'progress': {
                'questions_answered_today': self.questions_answered_today,
                'accuracy_rate': self.accuracy_rate,
                'streak_days': self.streak_days
            }
        }

        if self.next_review_date:
            data['next_review'] = {
                'date': self.next_review_date.isoformat(),
                'interval_days': self.new_interval_days
            }

        if self.new_achievements:
            data['achievements'] = self.new_achievements

        return data


@dataclass
class HintResponse:
    """Hint response."""

    hint_text: str
    hint_level: int  # 1-3
    hints_remaining: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'hint': self.hint_text,
            'level': self.hint_level,
            'remaining': self.hints_remaining
        }