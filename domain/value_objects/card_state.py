"""Spaced repetition card state value objects."""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional


class CardState(str, Enum):
    """State of a spaced repetition card."""

    NEW = "new"  # Never reviewed
    LEARNING = "learning"  # In initial learning phase
    REVIEW = "review"  # In regular review cycle
    RELEARNING = "relearning"  # Failed and needs relearning
    SUSPENDED = "suspended"  # Temporarily suspended
    BURIED = "buried"  # Buried until next day

    def can_review(self) -> bool:
        """Check if card can be reviewed."""
        return self not in {CardState.SUSPENDED, CardState.BURIED}

    def is_active(self) -> bool:
        """Check if card is active."""
        return self not in {CardState.SUSPENDED}


@dataclass(frozen=True)
class ReviewInterval:
    """Interval configuration for spaced repetition."""

    learning_steps: list[int]  # Steps in minutes for learning phase
    graduating_interval: int  # Days before graduating from learning
    easy_interval: int  # Days for easy bonus
    starting_ease: float  # Starting ease factor (default 2.5)
    easy_bonus: float  # Multiplier for easy answers
    interval_modifier: float  # Global interval modifier
    maximum_interval: int  # Maximum days between reviews
    leech_threshold: int  # Number of lapses before marking as leech

    @classmethod
    def default(cls) -> 'ReviewInterval':
        """Get default interval configuration (Anki-like)."""
        return cls(
            learning_steps=[1, 10],  # 1 min, 10 min
            graduating_interval=1,  # 1 day
            easy_interval=4,  # 4 days
            starting_ease=2.5,
            easy_bonus=1.3,
            interval_modifier=1.0,
            maximum_interval=36500,  # 100 years
            leech_threshold=8,
        )

    @classmethod
    def aggressive(cls) -> 'ReviewInterval':
        """Get aggressive interval configuration for faster learning."""
        return cls(
            learning_steps=[1, 5],
            graduating_interval=1,
            easy_interval=2,
            starting_ease=2.0,
            easy_bonus=1.15,
            interval_modifier=0.8,
            maximum_interval=180,
            leech_threshold=4,
        )

    @classmethod
    def relaxed(cls) -> 'ReviewInterval':
        """Get relaxed interval configuration for slower pace."""
        return cls(
            learning_steps=[5, 20, 60],
            graduating_interval=3,
            easy_interval=7,
            starting_ease=3.0,
            easy_bonus=1.5,
            interval_modifier=1.2,
            maximum_interval=36500,
            leech_threshold=12,
        )
