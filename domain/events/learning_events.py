"""Learning-related domain events."""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import UUID

from .base import LearningDomainEvent


@dataclass
class SessionStartedEvent(LearningDomainEvent):
    """Event fired when a learning session starts."""
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            'user_id': str(self.user_id),
            'session_id': str(self.session_id),
            'facet_id': str(self.facet_id) if self.facet_id else None
        }


@dataclass
class SessionCompletedEvent(LearningDomainEvent):
    """Event fired when a learning session completes."""
    
    questions_answered: int
    correct_answers: int
    accuracy_rate: float
    total_time_seconds: int
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            'user_id': str(self.user_id),
            'session_id': str(self.session_id),
            'facet_id': str(self.facet_id) if self.facet_id else None,
            'questions_answered': self.questions_answered,
            'correct_answers': self.correct_answers,
            'accuracy_rate': self.accuracy_rate,
            'total_time_seconds': self.total_time_seconds
        }


@dataclass
class SessionAbandonedEvent(LearningDomainEvent):
    """Event fired when a learning session is abandoned."""
    
    questions_answered: int
    time_spent_seconds: int
    abandon_reason: str = "timeout"
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            'user_id': str(self.user_id),
            'session_id': str(self.session_id),
            'facet_id': str(self.facet_id) if self.facet_id else None,
            'questions_answered': self.questions_answered,
            'time_spent_seconds': self.time_spent_seconds,
            'abandon_reason': self.abandon_reason
        }


@dataclass
class QuestionAnsweredEvent(LearningDomainEvent):
    """Event fired when a question is answered."""
    
    is_correct: bool
    time_taken_seconds: int
    difficulty_rating: Optional[int] = None
    confidence_level: Optional[int] = None
    hints_used: int = 0
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            'user_id': str(self.user_id),
            'session_id': str(self.session_id),
            'question_id': str(self.question_id),
            'facet_id': str(self.facet_id) if self.facet_id else None,
            'is_correct': self.is_correct,
            'time_taken_seconds': self.time_taken_seconds,
            'difficulty_rating': self.difficulty_rating,
            'confidence_level': self.confidence_level,
            'hints_used': self.hints_used
        }


@dataclass
class QuestionViewedEvent(LearningDomainEvent):
    """Event fired when a question is viewed."""
    
    question_type: str
    difficulty_level: int
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            'user_id': str(self.user_id),
            'session_id': str(self.session_id),
            'question_id': str(self.question_id),
            'facet_id': str(self.facet_id) if self.facet_id else None,
            'question_type': self.question_type,
            'difficulty_level': self.difficulty_level
        }


@dataclass
class HintRequestedEvent(LearningDomainEvent):
    """Event fired when a hint is requested."""
    
    hint_level: int
    total_hints_used: int
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            'user_id': str(self.user_id),
            'session_id': str(self.session_id),
            'question_id': str(self.question_id),
            'facet_id': str(self.facet_id) if self.facet_id else None,
            'hint_level': self.hint_level,
            'total_hints_used': self.total_hints_used
        }


@dataclass
class CardReviewedEvent(LearningDomainEvent):
    """Event fired when a spaced repetition card is reviewed."""
    
    card_id: UUID
    old_state: str
    new_state: str
    difficulty_rating: int
    old_interval_days: int
    new_interval_days: int
    old_due_date: datetime
    new_due_date: datetime
    ease_factor: float
    review_time_seconds: int
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            'user_id': str(self.user_id),
            'card_id': str(self.card_id),
            'question_id': str(self.question_id),
            'old_state': self.old_state,
            'new_state': self.new_state,
            'difficulty_rating': self.difficulty_rating,
            'old_interval_days': self.old_interval_days,
            'new_interval_days': self.new_interval_days,
            'old_due_date': self.old_due_date.isoformat(),
            'new_due_date': self.new_due_date.isoformat(),
            'ease_factor': self.ease_factor,
            'review_time_seconds': self.review_time_seconds
        }


@dataclass
class FacetCompletedEvent(LearningDomainEvent):
    """Event fired when a user completes all questions in a facet."""
    
    completion_percentage: float
    total_questions: int
    time_to_complete_days: int
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            'user_id': str(self.user_id),
            'facet_id': str(self.facet_id),
            'completion_percentage': self.completion_percentage,
            'total_questions': self.total_questions,
            'time_to_complete_days': self.time_to_complete_days
        }


@dataclass
class FacetMasteredEvent(LearningDomainEvent):
    """Event fired when a user masters a facet (80%+ mastery score)."""
    
    mastery_score: float
    accuracy_rate: float
    time_to_master_days: int
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            'user_id': str(self.user_id),
            'facet_id': str(self.facet_id),
            'mastery_score': self.mastery_score,
            'accuracy_rate': self.accuracy_rate,
            'time_to_master_days': self.time_to_master_days
        }


@dataclass
class StreakUpdatedEvent(LearningDomainEvent):
    """Event fired when a user's study streak is updated."""
    
    old_streak_days: int
    new_streak_days: int
    is_milestone: bool = False
    milestone_days: Optional[int] = None
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            'user_id': str(self.user_id),
            'facet_id': str(self.facet_id) if self.facet_id else None,
            'old_streak_days': self.old_streak_days,
            'new_streak_days': self.new_streak_days,
            'is_milestone': self.is_milestone,
            'milestone_days': self.milestone_days
        }


@dataclass
class AchievementUnlockedEvent(LearningDomainEvent):
    """Event fired when a user unlocks an achievement."""
    
    achievement_name: str
    achievement_display_name: str
    achievement_points: int
    achievement_type: str
    criteria_met: Dict[str, Any]
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            'user_id': str(self.user_id),
            'achievement_name': self.achievement_name,
            'achievement_display_name': self.achievement_display_name,
            'achievement_points': self.achievement_points,
            'achievement_type': self.achievement_type,
            'criteria_met': self.criteria_met
        }


@dataclass
class LearningGoalSetEvent(LearningDomainEvent):
    """Event fired when a user sets a learning goal."""
    
    goal_type: str  # daily_questions, weekly_time, facet_mastery, etc.
    goal_value: int
    target_date: Optional[datetime] = None
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            'user_id': str(self.user_id),
            'goal_type': self.goal_type,
            'goal_value': self.goal_value,
            'target_date': self.target_date.isoformat() if self.target_date else None
        }


@dataclass
class LearningGoalAchievedEvent(LearningDomainEvent):
    """Event fired when a user achieves a learning goal."""
    
    goal_type: str
    goal_value: int
    actual_value: int
    days_to_achieve: int
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            'user_id': str(self.user_id),
            'goal_type': self.goal_type,
            'goal_value': self.goal_value,
            'actual_value': self.actual_value,
            'days_to_achieve': self.days_to_achieve
        }