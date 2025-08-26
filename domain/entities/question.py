"""Question entity."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from ..value_objects import (
    QuestionType,
    QuestionSource,
    DifficultyLevel
)
from ..exceptions import EntityValidationException
from .base import Entity


@dataclass
class MCQOption:
    """Multiple choice question option."""

    key: str  # A, B, C, D
    text: str
    is_correct: bool = False
    explanation: Optional[str] = None

    def validate(self) -> None:
        """Validate option."""
        if not self.key or not self.key.strip():
            raise EntityValidationException("Option key is required")

        if not self.text or not self.text.strip():
            raise EntityValidationException("Option text is required")

        if self.key not in ['A', 'B', 'C', 'D', 'E', 'F']:
            raise EntityValidationException(f"Invalid option key: {self.key}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'key': self.key,
            'text': self.text,
            'is_correct': self.is_correct,
            'explanation': self.explanation,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCQOption':
        """Create from dictionary."""
        return cls(
            key=data['key'],
            text=data['text'],
            is_correct=data.get('is_correct', False),
            explanation=data.get('explanation'),
        )


@dataclass
class QuestionMetadata:
    """Question metadata."""

    estimated_time_seconds: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    hints: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    difficulty_explanation: Optional[str] = None
    learning_objectives: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)

    # Phase 2 fields
    ai_generated: bool = False
    ai_difficulty_assessment: Optional[float] = None
    community_rating: Optional[float] = None
    times_answered: int = 0
    average_time_seconds: Optional[float] = None
    success_rate: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'estimated_time_seconds': self.estimated_time_seconds,
            'tags': self.tags,
            'hints': self.hints,
            'references': self.references,
            'difficulty_explanation': self.difficulty_explanation,
            'learning_objectives': self.learning_objectives,
            'prerequisites': self.prerequisites,
            'ai_generated': self.ai_generated,
            'ai_difficulty_assessment': self.ai_difficulty_assessment,
            'community_rating': self.community_rating,
            'times_answered': self.times_answered,
            'average_time_seconds': self.average_time_seconds,
            'success_rate': self.success_rate,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QuestionMetadata':
        """Create from dictionary."""
        return cls(
            estimated_time_seconds=data.get('estimated_time_seconds'),
            tags=data.get('tags', []),
            hints=data.get('hints', []),
            references=data.get('references', []),
            difficulty_explanation=data.get('difficulty_explanation'),
            learning_objectives=data.get('learning_objectives', []),
            prerequisites=data.get('prerequisites', []),
            ai_generated=data.get('ai_generated', False),
            ai_difficulty_assessment=data.get('ai_difficulty_assessment'),
            community_rating=data.get('community_rating'),
            times_answered=data.get('times_answered', 0),
            average_time_seconds=data.get('average_time_seconds'),
            success_rate=data.get('success_rate'),
        )


@dataclass
class Question(Entity):
    """Question entity."""

    external_id: str
    facet_id: UUID
    type: QuestionType
    question_text: str
    difficulty_level: DifficultyLevel
    source: QuestionSource
    metadata: QuestionMetadata = field(default_factory=QuestionMetadata)
    is_active: bool = True

    # MCQ specific fields
    options: List[MCQOption] = field(default_factory=list)

    # Theory/Scenario specific fields
    sample_answer: Optional[str] = None
    evaluation_criteria: Optional[str] = None

    def validate(self) -> None:
        """Validate question entity."""
        if not self.external_id or not self.external_id.strip():
            raise EntityValidationException("External ID is required")

        if not self.question_text or not self.question_text.strip():
            raise EntityValidationException("Question text is required")

        if self.type == QuestionType.MCQ:
            if not self.options:
                raise EntityValidationException("MCQ questions must have options")

            if len(self.options) < 2:
                raise EntityValidationException("MCQ questions must have at least 2 options")

            correct_options = [opt for opt in self.options if opt.is_correct]
            if len(correct_options) != 1:
                raise EntityValidationException("MCQ questions must have exactly one correct option")

            # Validate each option
            for option in self.options:
                option.validate()

            # Check for duplicate keys
            keys = [opt.key for opt in self.options]
            if len(keys) != len(set(keys)):
                raise EntityValidationException("MCQ options must have unique keys")

    def is_mcq(self) -> bool:
        """Check if this is an MCQ question."""
        return self.type == QuestionType.MCQ

    def get_correct_answer(self) -> Optional[str]:
        """Get correct answer for MCQ."""
        if not self.is_mcq():
            return None

        for option in self.options:
            if option.is_correct:
                return option.key
        return None

    def get_explanation(self) -> Optional[str]:
        """Get explanation for correct answer."""
        if not self.is_mcq():
            return self.sample_answer

        for option in self.options:
            if option.is_correct and option.explanation:
                return option.explanation
        return None

    def check_answer(self, answer: str) -> bool:
        """Check if answer is correct (for MCQ only)."""
        if not self.is_mcq():
            raise EntityValidationException("Cannot auto-check non-MCQ questions")

        return answer == self.get_correct_answer()

    def get_estimated_time(self) -> int:
        """Get estimated time in seconds."""
        if self.metadata.estimated_time_seconds:
            return self.metadata.estimated_time_seconds
        return self.type.default_time_seconds()

    def update_statistics(self, time_taken: int, is_correct: bool) -> None:
        """Update question statistics."""
        self.metadata.times_answered += 1

        # Update average time
        if self.metadata.average_time_seconds is None:
            self.metadata.average_time_seconds = float(time_taken)
        else:
            # Running average
            self.metadata.average_time_seconds = (
                (self.metadata.average_time_seconds * (self.metadata.times_answered - 1) + time_taken)
                / self.metadata.times_answered
            )

        # Update success rate
        if self.metadata.success_rate is None:
            self.metadata.success_rate = 100.0 if is_correct else 0.0
        else:
            # Running average
            current_correct = (self.metadata.success_rate / 100.0) * (self.metadata.times_answered - 1)
            if is_correct:
                current_correct += 1
            self.metadata.success_rate = (current_correct / self.metadata.times_answered) * 100.0

        self.update_timestamp()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = super().to_dict()
        data.update({
            'external_id': self.external_id,
            'facet_id': str(self.facet_id),
            'type': self.type.value,
            'question_text': self.question_text,
            'difficulty_level': self.difficulty_level.value,
            'source': self.source.value,
            'metadata': self.metadata.to_dict(),
            'is_active': self.is_active,
            'options': [opt.to_dict() for opt in self.options],
            'sample_answer': self.sample_answer,
            'evaluation_criteria': self.evaluation_criteria,
        })
        return data