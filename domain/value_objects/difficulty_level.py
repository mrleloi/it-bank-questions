"""Difficulty-related value objects."""

from enum import IntEnum
from dataclasses import dataclass
from typing import ClassVar, Dict


class DifficultyLevel(IntEnum):
    """Question difficulty levels."""

    VERY_EASY = 1
    EASY = 2
    MEDIUM = 3
    HARD = 4
    VERY_HARD = 5

    @classmethod
    def from_string(cls, value: str) -> 'DifficultyLevel':
        """Create from string representation."""
        mapping = {
            'very_easy': cls.VERY_EASY,
            'easy': cls.EASY,
            'medium': cls.MEDIUM,
            'hard': cls.HARD,
            'very_hard': cls.VERY_HARD,
        }
        return mapping.get(value.lower(), cls.MEDIUM)

    def to_multiplier(self) -> float:
        """Convert to difficulty multiplier for scoring."""
        multipliers = {
            self.VERY_EASY: 0.5,
            self.EASY: 0.75,
            self.MEDIUM: 1.0,
            self.HARD: 1.25,
            self.VERY_HARD: 1.5,
        }
        return multipliers[self]


class DifficultyRating(IntEnum):
    """User's rating of question difficulty after answering."""

    EASY = 1  # "Too easy, I knew it immediately"
    MEDIUM = 2  # "Just right, had to think"
    HARD = 3  # "Difficult, struggled but got it"
    VERY_HARD = 4  # "Too hard, didn't know"

    def to_ease_factor_modifier(self) -> float:
        """Convert to ease factor modifier for spaced repetition."""
        modifiers = {
            self.EASY: 0.15,
            self.MEDIUM: 0.0,
            self.HARD: -0.15,
            self.VERY_HARD: -0.3,
        }
        return modifiers[self]

    def to_interval_modifier(self) -> float:
        """Convert to interval modifier for next review."""
        modifiers = {
            self.EASY: 1.3,
            self.MEDIUM: 1.0,
            self.HARD: 0.6,
            self.VERY_HARD: 0.0,  # Review again immediately
        }
        return modifiers[self]
