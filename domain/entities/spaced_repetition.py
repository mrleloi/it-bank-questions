"""Spaced repetition card entity."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID
import math

from ..value_objects import (
    CardState,
    DifficultyRating,
    ReviewInterval
)
from ..exceptions import (
    EntityValidationException,
    InvalidStateTransitionException
)
from .base import Entity


@dataclass
class CardStatistics:
    """Statistics for a spaced repetition card."""

    total_reviews: int = 0
    total_correct: int = 0
    total_time_seconds: int = 0
    lapses: int = 0  # Number of times forgotten
    last_ease_factor: float = 2.5
    last_interval_days: int = 0

    @property
    def accuracy_rate(self) -> float:
        """Calculate accuracy rate."""
        if self.total_reviews == 0:
            return 0.0
        return (self.total_correct / self.total_reviews) * 100.0

    @property
    def average_time_seconds(self) -> float:
        """Calculate average review time."""
        if self.total_reviews == 0:
            return 0.0
        return self.total_time_seconds / self.total_reviews

    def is_leech(self, threshold: int = 8) -> bool:
        """Check if card is a leech (difficult card)."""
        return self.lapses >= threshold

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'total_reviews': self.total_reviews,
            'total_correct': self.total_correct,
            'total_time_seconds': self.total_time_seconds,
            'lapses': self.lapses,
            'last_ease_factor': self.last_ease_factor,
            'last_interval_days': self.last_interval_days,
            'accuracy_rate': self.accuracy_rate,
            'average_time_seconds': self.average_time_seconds,
        }


@dataclass
class SpacedRepetitionCard(Entity):
    """Spaced repetition card for a question."""

    user_id: UUID
    question_id: UUID
    state: CardState = CardState.NEW
    ease_factor: float = 2.5
    interval_days: int = 0
    due_date: datetime = field(default_factory=datetime.now)
    last_reviewed_at: Optional[datetime] = None
    statistics: CardStatistics = field(default_factory=CardStatistics)
    review_config: ReviewInterval = field(default_factory=ReviewInterval.default)

    # Learning phase specific
    learning_step: int = 0  # Current step in learning phase

    def validate(self) -> None:
        """Validate card entity."""
        if self.ease_factor < 1.3:
            raise EntityValidationException("Ease factor cannot be less than 1.3")

        if self.ease_factor > 5.0:
            raise EntityValidationException("Ease factor cannot be greater than 5.0")

        if self.interval_days < 0:
            raise EntityValidationException("Interval cannot be negative")

    def can_review(self) -> bool:
        """Check if card can be reviewed now."""
        if not self.state.can_review():
            return False

        return datetime.now() >= self.due_date

    def is_overdue(self) -> bool:
        """Check if card is overdue."""
        if not self.state.can_review():
            return False

        return datetime.now() > self.due_date + timedelta(days=1)

    def calculate_next_interval(self, rating: DifficultyRating) -> int:
        """
        Calculate next interval based on SM-2 algorithm.

        Args:
            rating: User's difficulty rating

        Returns:
            Next interval in days
        """
        if self.state == CardState.NEW:
            # First review
            if rating == DifficultyRating.VERY_HARD:
                return 0  # Review again today
            elif rating == DifficultyRating.HARD:
                return 1
            elif rating == DifficultyRating.MEDIUM:
                return self.review_config.graduating_interval
            else:  # EASY
                return self.review_config.easy_interval

        elif self.state == CardState.LEARNING:
            # Still in learning phase
            if rating == DifficultyRating.VERY_HARD:
                # Reset to first step
                self.learning_step = 0
                return 0
            elif rating == DifficultyRating.HARD:
                # Stay at current step
                return self._get_current_learning_interval()
            elif rating == DifficultyRating.MEDIUM:
                # Move to next step
                self.learning_step += 1
                if self.learning_step >= len(self.review_config.learning_steps):
                    # Graduate from learning
                    return self.review_config.graduating_interval
                return self._get_current_learning_interval()
            else:  # EASY
                # Graduate immediately with bonus
                return self.review_config.easy_interval

        else:  # REVIEW or RELEARNING
            # Calculate new interval based on ease factor
            if rating == DifficultyRating.VERY_HARD:
                # Lapse - reset interval
                new_interval = 1
                self.statistics.lapses += 1
            else:
                # Apply ease factor
                modifier = rating.to_interval_modifier()
                new_interval = int(
                    self.interval_days *
                    self.ease_factor *
                    modifier *
                    self.review_config.interval_modifier
                )

                if rating == DifficultyRating.EASY:
                    new_interval = int(new_interval * self.review_config.easy_bonus)

            # Cap at maximum interval
            new_interval = min(new_interval, self.review_config.maximum_interval)

            return max(1, new_interval)  # At least 1 day

    def review(self, rating: DifficultyRating, time_seconds: int) -> None:
        """
        Process a review of this card.

        Args:
            rating: User's difficulty rating
            time_seconds: Time taken to answer
        """
        # Update ease factor (except for new cards)
        if self.state != CardState.NEW:
            ease_modifier = rating.to_ease_factor_modifier()
            self.ease_factor = max(1.3, self.ease_factor + ease_modifier)
            self.ease_factor = min(5.0, self.ease_factor)

        # Calculate next interval
        self.interval_days = self.calculate_next_interval(rating)

        # Update state
        if self.state == CardState.NEW:
            if rating == DifficultyRating.VERY_HARD:
                self.state = CardState.LEARNING
                self.learning_step = 0
            elif rating in {DifficultyRating.HARD, DifficultyRating.MEDIUM}:
                self.state = CardState.LEARNING
                self.learning_step = 0
            else:  # EASY
                self.state = CardState.REVIEW

        elif self.state == CardState.LEARNING:
            if self.learning_step >= len(self.review_config.learning_steps):
                self.state = CardState.REVIEW

        elif self.state == CardState.REVIEW:
            if rating == DifficultyRating.VERY_HARD:
                self.state = CardState.RELEARNING
                self.learning_step = 0

        elif self.state == CardState.RELEARNING:
            if rating != DifficultyRating.VERY_HARD:
                self.state = CardState.REVIEW

        # Update due date
        if self.interval_days == 0:
            # Review again in a few minutes
            minutes = self._get_current_learning_interval()
            self.due_date = datetime.now() + timedelta(minutes=minutes)
        else:
            self.due_date = datetime.now() + timedelta(days=self.interval_days)

        # Update statistics
        self.statistics.total_reviews += 1
        if rating != DifficultyRating.VERY_HARD:
            self.statistics.total_correct += 1
        self.statistics.total_time_seconds += time_seconds
        self.statistics.last_ease_factor = self.ease_factor
        self.statistics.last_interval_days = self.interval_days

        # Update timestamps
        self.last_reviewed_at = datetime.now()
        self.update_timestamp()

    def _get_current_learning_interval(self) -> int:
        """Get current learning interval in minutes."""
        if self.learning_step < len(self.review_config.learning_steps):
            return self.review_config.learning_steps[self.learning_step]
        return self.review_config.learning_steps[-1] if self.review_config.learning_steps else 10

    def suspend(self) -> None:
        """Suspend this card."""
        if self.state == CardState.SUSPENDED:
            raise InvalidStateTransitionException("Card is already suspended")
        self.state = CardState.SUSPENDED
        self.update_timestamp()

    def unsuspend(self) -> None:
        """Unsuspend this card."""
        if self.state != CardState.SUSPENDED:
            raise InvalidStateTransitionException("Card is not suspended")
        self.state = CardState.REVIEW
        self.update_timestamp()

    def bury(self) -> None:
        """Bury this card until tomorrow."""
        if self.state == CardState.BURIED:
            raise InvalidStateTransitionException("Card is already buried")
        self.state = CardState.BURIED
        self.due_date = datetime.now().replace(hour=0, minute=0, second=0) + timedelta(days=1)
        self.update_timestamp()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = super().to_dict()
        data.update({
            'user_id': str(self.user_id),
            'question_id': str(self.question_id),
            'state': self.state.value,
            'ease_factor': self.ease_factor,
            'interval_days': self.interval_days,
            'due_date': self.due_date.isoformat(),
            'last_reviewed_at': self.last_reviewed_at.isoformat() if self.last_reviewed_at else None,
            'statistics': self.statistics.to_dict(),
            'learning_step': self.learning_step,
            'is_overdue': self.is_overdue(),
            'can_review': self.can_review(),
        })
        return data