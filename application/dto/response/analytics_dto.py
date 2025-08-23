"""Analytics-related response DTOs."""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import datetime


@dataclass
class StudyPatternResponse:
    """Study pattern analysis response."""

    peak_hour: Optional[int]
    peak_day: Optional[str]
    hourly_distribution: Dict[int, int]
    daily_distribution: Dict[str, int]
    consistency_score: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'peak_hour': self.peak_hour,
            'peak_day': self.peak_day,
            'distributions': {
                'hourly': self.hourly_distribution,
                'daily': self.daily_distribution
            },
            'consistency_score': self.consistency_score
        }


@dataclass
class PerformanceTrendResponse:
    """Performance trend response."""

    trend: str  # improving, declining, stable
    improvement_rate: float
    recent_accuracy: float
    average_accuracy: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'trend': self.trend,
            'improvement_rate': self.improvement_rate,
            'accuracy': {
                'recent': self.recent_accuracy,
                'average': self.average_accuracy
            }
        }


@dataclass
class LearningVelocityResponse:
    """Learning velocity response."""

    questions_per_day: float
    mastery_growth_rate: float
    estimated_completion_days: Optional[int]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'questions_per_day': self.questions_per_day,
            'mastery_growth_rate': self.mastery_growth_rate,
            'estimated_completion_days': self.estimated_completion_days
        }


@dataclass
class CompletionPredictionResponse:
    """Completion prediction response."""

    status: str  # not_started, in_progress, inactive
    estimated_days: Optional[int]
    completion_date: Optional[str]
    confidence: float
    remaining_questions: int
    daily_average: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'status': self.status,
            'prediction': {
                'days': self.estimated_days,
                'date': self.completion_date,
                'confidence': self.confidence
            },
            'details': {
                'remaining_questions': self.remaining_questions,
                'daily_average': self.daily_average
            }
        }
