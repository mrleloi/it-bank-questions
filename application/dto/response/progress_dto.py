"""Progress-related response DTOs."""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID


@dataclass
class FacetProgressResponse:
    """Facet progress response."""

    facet_id: UUID
    facet_name: str
    total_questions: int
    seen_questions: int
    mastered_questions: int
    completion_percentage: float
    mastery_score: float
    mastery_level: str
    accuracy_rate: float
    current_streak_days: int
    last_activity_at: Optional[datetime]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'facet_id': str(self.facet_id),
            'facet_name': self.facet_name,
            'questions': {
                'total': self.total_questions,
                'seen': self.seen_questions,
                'mastered': self.mastered_questions
            },
            'progress': {
                'completion': self.completion_percentage,
                'mastery': self.mastery_score,
                'level': self.mastery_level,
                'accuracy': self.accuracy_rate
            },
            'streak_days': self.current_streak_days,
            'last_activity': self.last_activity_at.isoformat() if self.last_activity_at else None
        }


@dataclass
class UserProgressResponse:
    """User progress response."""

    user_id: UUID
    overall_mastery_score: float
    total_study_time_seconds: int
    total_questions_answered: int
    total_correct_answers: int
    achievement_points: int
    facet_progresses: List[FacetProgressResponse]

    # Learning patterns
    preferred_study_time: Optional[str]
    average_session_length_minutes: float
    most_productive_day: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'user_id': str(self.user_id),
            'overall': {
                'mastery_score': self.overall_mastery_score,
                'total_study_time_seconds': self.total_study_time_seconds,
                'total_questions_answered': self.total_questions_answered,
                'total_correct_answers': self.total_correct_answers,
                'achievement_points': self.achievement_points
            },
            'facets': [fp.to_dict() for fp in self.facet_progresses],
            'patterns': {
                'preferred_study_time': self.preferred_study_time,
                'average_session_minutes': self.average_session_length_minutes,
                'most_productive_day': self.most_productive_day
            }
        }


@dataclass
class LeaderboardEntryResponse:
    """Leaderboard entry response."""

    rank: int
    user_id: UUID
    username: str
    mastery_score: float
    achievement_points: int
    total_questions_answered: int
    streak_days: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'rank': self.rank,
            'user': {
                'id': str(self.user_id),
                'username': self.username
            },
            'stats': {
                'mastery_score': self.mastery_score,
                'achievement_points': self.achievement_points,
                'total_questions': self.total_questions_answered,
                'streak_days': self.streak_days
            }
        }