"""Learning metrics value objects."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from enum import Enum


class MasteryLevel(str, Enum):
    """User's mastery level for a topic."""

    NOVICE = "novice"  # 0-20% mastery
    BEGINNER = "beginner"  # 20-40% mastery
    INTERMEDIATE = "intermediate"  # 40-60% mastery
    ADVANCED = "advanced"  # 60-80% mastery
    EXPERT = "expert"  # 80-100% mastery

    @classmethod
    def from_score(cls, score: float) -> 'MasteryLevel':
        """Determine mastery level from score (0-100)."""
        if score < 20:
            return cls.NOVICE
        elif score < 40:
            return cls.BEGINNER
        elif score < 60:
            return cls.INTERMEDIATE
        elif score < 80:
            return cls.ADVANCED
        else:
            return cls.EXPERT

    def minimum_score(self) -> float:
        """Get minimum score for this level."""
        scores = {
            self.NOVICE: 0,
            self.BEGINNER: 20,
            self.INTERMEDIATE: 40,
            self.ADVANCED: 60,
            self.EXPERT: 80,
        }
        return scores[self]


@dataclass(frozen=True)
class LearningMetrics:
    """Comprehensive learning metrics for a user."""

    total_questions_seen: int
    total_questions_answered: int
    correct_answers: int
    total_time_spent_seconds: int
    average_response_time_seconds: float
    streak_days: int
    last_activity: datetime
    mastery_score: float  # 0-100

    @property
    def accuracy_rate(self) -> float:
        """Calculate accuracy rate."""
        if self.total_questions_answered == 0:
            return 0.0
        return (self.correct_answers / self.total_questions_answered) * 100

    @property
    def completion_rate(self) -> float:
        """Calculate completion rate."""
        if self.total_questions_seen == 0:
            return 0.0
        return (self.total_questions_answered / self.total_questions_seen) * 100

    @property
    def mastery_level(self) -> MasteryLevel:
        """Get mastery level based on score."""
        return MasteryLevel.from_score(self.mastery_score)

    @property
    def is_active(self) -> bool:
        """Check if user is actively learning."""
        days_inactive = (datetime.now() - self.last_activity).days
        return days_inactive <= 7

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'total_questions_seen': self.total_questions_seen,
            'total_questions_answered': self.total_questions_answered,
            'correct_answers': self.correct_answers,
            'total_time_spent_seconds': self.total_time_spent_seconds,
            'average_response_time_seconds': self.average_response_time_seconds,
            'streak_days': self.streak_days,
            'last_activity': self.last_activity.isoformat(),
            'mastery_score': self.mastery_score,
            'accuracy_rate': self.accuracy_rate,
            'completion_rate': self.completion_rate,
            'mastery_level': self.mastery_level.value,
            'is_active': self.is_active,
        }


@dataclass(frozen=True)
class PerformanceMetrics:
    """Performance metrics for a specific time period."""

    period_start: datetime
    period_end: datetime
    questions_answered: int
    correct_answers: int
    average_difficulty: float
    improvement_rate: float  # Compared to previous period

    @property
    def period_accuracy(self) -> float:
        """Calculate accuracy for this period."""
        if self.questions_answered == 0:
            return 0.0
        return (self.correct_answers / self.questions_answered) * 100

    @property
    def is_improving(self) -> bool:
        """Check if performance is improving."""
        return self.improvement_rate > 0


@dataclass(frozen=True)
class TimeMetrics:
    """Time-based metrics for learning sessions."""

    total_time_seconds: int
    active_time_seconds: int
    idle_time_seconds: int
    average_question_time_seconds: float
    fastest_response_seconds: float
    slowest_response_seconds: float

    @property
    def efficiency_rate(self) -> float:
        """Calculate time efficiency rate."""
        if self.total_time_seconds == 0:
            return 0.0
        return (self.active_time_seconds / self.total_time_seconds) * 100

    @property
    def formatted_total_time(self) -> str:
        """Get formatted total time."""
        td = timedelta(seconds=self.total_time_seconds)
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
