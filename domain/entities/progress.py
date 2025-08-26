"""Progress tracking entities."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from uuid import UUID

from ..value_objects import MasteryLevel
from ..exceptions import EntityValidationException
from .base import Entity


@dataclass
class FacetProgress(Entity):
    """Progress for a specific facet."""

    user_id: UUID
    facet_id: UUID
    total_questions: int = 0
    seen_questions: int = 0
    mastered_questions: int = 0
    mastery_score: float = 0.0
    last_activity_at: Optional[datetime] = None
    total_time_spent_seconds: int = 0

    # Performance metrics
    accuracy_rate: float = 0.0
    average_response_time: float = 0.0
    difficulty_comfort: float = 3.0  # 1-5 scale

    # Streak tracking
    current_streak_days: int = 0
    longest_streak_days: int = 0
    last_streak_date: Optional[datetime] = None

    def validate(self) -> None:
        """Validate progress entity."""
        if self.mastery_score < 0 or self.mastery_score > 100:
            raise EntityValidationException("Mastery score must be between 0 and 100")

        if self.accuracy_rate < 0 or self.accuracy_rate > 100:
            raise EntityValidationException("Accuracy rate must be between 0 and 100")

        if self.difficulty_comfort < 1 or self.difficulty_comfort > 5:
            raise EntityValidationException("Difficulty comfort must be between 1 and 5")

    @property
    def mastery_level(self) -> MasteryLevel:
        """Get mastery level based on score."""
        return MasteryLevel.from_score(self.mastery_score)

    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage."""
        if self.total_questions == 0:
            return 0.0
        return (self.seen_questions / self.total_questions) * 100.0

    @property
    def mastery_percentage(self) -> float:
        """Calculate mastery percentage."""
        if self.total_questions == 0:
            return 0.0
        return (self.mastered_questions / self.total_questions) * 100.0

    def is_complete(self) -> bool:
        """Check if facet is complete."""
        return self.seen_questions >= self.total_questions

    def is_mastered(self) -> bool:
        """Check if facet is mastered."""
        return self.mastery_score >= 80.0

    def update_streak(self, studied_today: bool = True) -> None:
        """Update streak information."""
        today = datetime.now().date()

        if self.last_streak_date:
            last_date = self.last_streak_date.date()
            days_diff = (today - last_date).days

            if days_diff == 0:
                # Already studied today
                return
            elif days_diff == 1 and studied_today:
                # Continuing streak
                self.current_streak_days += 1
            elif days_diff > 1 and studied_today:
                # Broken streak, start new one
                self.current_streak_days = 1
            else:
                # Broken streak
                self.current_streak_days = 0
        elif studied_today:
            # First time studying
            self.current_streak_days = 1

        if studied_today:
            self.last_streak_date = datetime.now()
            if self.current_streak_days > self.longest_streak_days:
                self.longest_streak_days = self.current_streak_days

        self.update_timestamp()

    def add_study_time(self, seconds: int) -> None:
        """Add study time."""
        self.total_time_spent_seconds += seconds
        self.last_activity_at = datetime.now()
        self.update_timestamp()

    def update_performance(
        self,
        correct: bool,
        response_time: float,
        difficulty: int
    ) -> None:
        """Update performance metrics."""
        # Update accuracy (running average)
        weight = 0.1  # Weight for new data point
        if correct:
            self.accuracy_rate = (1 - weight) * self.accuracy_rate + weight * 100
        else:
            self.accuracy_rate = (1 - weight) * self.accuracy_rate

        # Update average response time
        self.average_response_time = (
            (1 - weight) * self.average_response_time + weight * response_time
        )

        # Update difficulty comfort based on performance
        if correct:
            if difficulty > self.difficulty_comfort:
                # Correctly answered harder question, increase comfort
                self.difficulty_comfort = min(5.0, self.difficulty_comfort + 0.1)
        else:
            if difficulty <= self.difficulty_comfort:
                # Failed easier question, decrease comfort
                self.difficulty_comfort = max(1.0, self.difficulty_comfort - 0.1)

        self.update_timestamp()

    def calculate_mastery_score(self) -> None:
        """Calculate overall mastery score."""
        # Weighted calculation:
        # - 40% from questions mastered
        # - 30% from accuracy rate
        # - 20% from completion
        # - 10% from consistency (streak)

        mastery_weight = 0.4 * self.mastery_percentage
        accuracy_weight = 0.3 * self.accuracy_rate
        completion_weight = 0.2 * self.completion_percentage

        # Streak bonus (max 10%)
        streak_bonus = min(10.0, self.current_streak_days / 3.0)

        self.mastery_score = min(100.0,
            mastery_weight + accuracy_weight + completion_weight + streak_bonus
        )
        self.update_timestamp()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = super().to_dict()
        data.update({
            'user_id': str(self.user_id),
            'facet_id': str(self.facet_id),
            'total_questions': self.total_questions,
            'seen_questions': self.seen_questions,
            'mastered_questions': self.mastered_questions,
            'mastery_score': self.mastery_score,
            'mastery_level': self.mastery_level.value,
            'last_activity_at': self.last_activity_at.isoformat() if self.last_activity_at else None,
            'total_time_spent_seconds': self.total_time_spent_seconds,
            'accuracy_rate': self.accuracy_rate,
            'average_response_time': self.average_response_time,
            'difficulty_comfort': self.difficulty_comfort,
            'current_streak_days': self.current_streak_days,
            'longest_streak_days': self.longest_streak_days,
            'completion_percentage': self.completion_percentage,
            'mastery_percentage': self.mastery_percentage,
            'is_complete': self.is_complete(),
            'is_mastered': self.is_mastered(),
        })
        return data


@dataclass
class UserProgress(Entity):
    """Overall user progress across all content."""

    user_id: UUID
    facet_progresses: Dict[UUID, FacetProgress] = field(default_factory=dict)

    # Global metrics
    total_study_time_seconds: int = 0
    total_questions_answered: int = 0
    total_correct_answers: int = 0
    overall_mastery_score: float = 0.0

    # Achievements
    achievements_unlocked: List[str] = field(default_factory=list)
    achievement_points: int = 0

    # Learning patterns
    preferred_study_time: Optional[str] = None  # e.g., "morning", "evening"
    average_session_length_minutes: float = 0.0
    most_productive_day: Optional[str] = None  # Day of week

    def validate(self) -> None:
        """Validate user progress."""
        if self.overall_mastery_score < 0 or self.overall_mastery_score > 100:
            raise EntityValidationException("Overall mastery score must be between 0 and 100")

    def get_facet_progress(self, facet_id: UUID) -> Optional[FacetProgress]:
        """Get progress for a specific facet."""
        return self.facet_progresses.get(facet_id)

    def add_facet_progress(self, progress: FacetProgress) -> None:
        """Add or update facet progress."""
        if progress.user_id != self.user_id:
            raise EntityValidationException("Progress user_id doesn't match")

        self.facet_progresses[progress.facet_id] = progress
        self.recalculate_overall_mastery()
        self.update_timestamp()

    def recalculate_overall_mastery(self) -> None:
        """Recalculate overall mastery score."""
        if not self.facet_progresses:
            self.overall_mastery_score = 0.0
            return

        total_score = sum(p.mastery_score for p in self.facet_progresses.values())
        self.overall_mastery_score = total_score / len(self.facet_progresses)

    def check_achievements(self) -> List[str]:
        """Check and unlock new achievements."""
        new_achievements = []

        # Check various achievement conditions
        if self.total_questions_answered >= 100 and "century_club" not in self.achievements_unlocked:
            self.achievements_unlocked.append("century_club")
            new_achievements.append("century_club")
            self.achievement_points += 50

        if self.overall_mastery_score >= 80 and "master_learner" not in self.achievements_unlocked:
            self.achievements_unlocked.append("master_learner")
            new_achievements.append("master_learner")
            self.achievement_points += 100

        # Check streak achievements
        max_streak = max(
            (p.current_streak_days for p in self.facet_progresses.values()),
            default=0
        )

        if max_streak >= 7 and "week_warrior" not in self.achievements_unlocked:
            self.achievements_unlocked.append("week_warrior")
            new_achievements.append("week_warrior")
            self.achievement_points += 25

        if max_streak >= 30 and "monthly_master" not in self.achievements_unlocked:
            self.achievements_unlocked.append("monthly_master")
            new_achievements.append("monthly_master")
            self.achievement_points += 75

        return new_achievements

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = super().to_dict()
        data.update({
            'user_id': str(self.user_id),
            'facet_progresses': {
                str(k): v.to_dict() for k, v in self.facet_progresses.items()
            },
            'total_study_time_seconds': self.total_study_time_seconds,
            'total_questions_answered': self.total_questions_answered,
            'total_correct_answers': self.total_correct_answers,
            'overall_mastery_score': self.overall_mastery_score,
            'achievements_unlocked': self.achievements_unlocked,
            'achievement_points': self.achievement_points,
            'preferred_study_time': self.preferred_study_time,
            'average_session_length_minutes': self.average_session_length_minutes,
            'most_productive_day': self.most_productive_day,
        })
        return data