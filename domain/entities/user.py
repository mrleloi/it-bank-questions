"""User entity."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from ..value_objects import UserRole, UserStatus, ReviewInterval
from ..exceptions import EntityValidationException
from .base import AggregateRoot


@dataclass
class UserPreferences:
    """User preferences."""

    theme: str = "light"
    language: str = "en"
    timezone: str = "UTC"
    email_notifications: bool = True
    daily_reminder: bool = True
    reminder_time: str = "09:00"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'theme': self.theme,
            'language': self.language,
            'timezone': self.timezone,
            'email_notifications': self.email_notifications,
            'daily_reminder': self.daily_reminder,
            'reminder_time': self.reminder_time,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserPreferences':
        """Create from dictionary."""
        return cls(
            theme=data.get('theme', 'light'),
            language=data.get('language', 'en'),
            timezone=data.get('timezone', 'UTC'),
            email_notifications=data.get('email_notifications', True),
            daily_reminder=data.get('daily_reminder', True),
            reminder_time=data.get('reminder_time', '09:00'),
        )


@dataclass
class LearningSettings:
    """User's learning settings."""

    daily_goal: int = 20  # Questions per day
    review_interval: ReviewInterval = field(default_factory=ReviewInterval.default)
    auto_play_audio: bool = False
    show_timer: bool = True
    enable_hints: bool = True
    difficulty_preference: str = "adaptive"  # adaptive, easy, medium, hard

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'daily_goal': self.daily_goal,
            'review_interval': {
                'learning_steps': self.review_interval.learning_steps,
                'graduating_interval': self.review_interval.graduating_interval,
                'easy_interval': self.review_interval.easy_interval,
                'starting_ease': self.review_interval.starting_ease,
                'easy_bonus': self.review_interval.easy_bonus,
                'interval_modifier': self.review_interval.interval_modifier,
                'maximum_interval': self.review_interval.maximum_interval,
                'leech_threshold': self.review_interval.leech_threshold,
            },
            'auto_play_audio': self.auto_play_audio,
            'show_timer': self.show_timer,
            'enable_hints': self.enable_hints,
            'difficulty_preference': self.difficulty_preference,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LearningSettings':
        """Create from dictionary."""
        review_data = data.get('review_interval', {})
        review_interval = ReviewInterval(
            learning_steps=review_data.get('learning_steps', [1, 10]),
            graduating_interval=review_data.get('graduating_interval', 1),
            easy_interval=review_data.get('easy_interval', 4),
            starting_ease=review_data.get('starting_ease', 2.5),
            easy_bonus=review_data.get('easy_bonus', 1.3),
            interval_modifier=review_data.get('interval_modifier', 1.0),
            maximum_interval=review_data.get('maximum_interval', 36500),
            leech_threshold=review_data.get('leech_threshold', 8),
        )

        return cls(
            daily_goal=data.get('daily_goal', 20),
            review_interval=review_interval,
            auto_play_audio=data.get('auto_play_audio', False),
            show_timer=data.get('show_timer', True),
            enable_hints=data.get('enable_hints', True),
            difficulty_preference=data.get('difficulty_preference', 'adaptive'),
        )


@dataclass
class User(AggregateRoot):
    """User aggregate root."""

    email: str
    username: str
    full_name: Optional[str] = None
    role: UserRole = UserRole.LEARNER
    status: UserStatus = UserStatus.PENDING
    preferences: UserPreferences = field(default_factory=UserPreferences)
    learning_settings: LearningSettings = field(default_factory=LearningSettings)
    last_login_at: Optional[datetime] = None
    email_verified_at: Optional[datetime] = None

    # Statistics
    total_study_time_seconds: int = 0
    total_questions_answered: int = 0
    current_streak_days: int = 0
    longest_streak_days: int = 0
    achievement_points: int = 0

    def validate(self) -> None:
        """Validate user entity."""
        if not self.email or '@' not in self.email:
            raise EntityValidationException("Invalid email address")

        if not self.username or len(self.username) < 3:
            raise EntityValidationException("Username must be at least 3 characters")

        if len(self.username) > 50:
            raise EntityValidationException("Username must be less than 50 characters")

        # Username should only contain alphanumeric and underscore
        if not self.username.replace('_', '').isalnum():
            raise EntityValidationException(
                "Username can only contain letters, numbers, and underscores"
            )

    def can_login(self) -> bool:
        """Check if user can login."""
        return self.status.can_login()

    def is_verified(self) -> bool:
        """Check if user email is verified."""
        return self.email_verified_at is not None

    def verify_email(self) -> None:
        """Mark email as verified."""
        self.email_verified_at = datetime.now()
        if self.status == UserStatus.PENDING:
            self.status = UserStatus.ACTIVE
        self.update_timestamp()

    def suspend(self, reason: str) -> None:
        """Suspend user account."""
        if self.status == UserStatus.ACTIVE:
            self.status = UserStatus.SUSPENDED
            self.add_domain_event(UserSuspendedEvent(self.id, reason))
            self.update_timestamp()

    def activate(self) -> None:
        """Activate user account."""
        if self.status in {UserStatus.PENDING, UserStatus.SUSPENDED}:
            self.status = UserStatus.ACTIVE
            self.update_timestamp()

    def update_login(self) -> None:
        """Update last login timestamp."""
        self.last_login_at = datetime.now()
        self.update_timestamp()

    def update_streak(self, answered_today: bool) -> None:
        """Update streak days."""
        if answered_today:
            self.current_streak_days += 1
            if self.current_streak_days > self.longest_streak_days:
                self.longest_streak_days = self.current_streak_days
        else:
            self.current_streak_days = 0
        self.update_timestamp()

    def add_study_time(self, seconds: int) -> None:
        """Add study time."""
        self.total_study_time_seconds += seconds
        self.update_timestamp()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = super().to_dict()
        data.update({
            'email': self.email,
            'username': self.username,
            'full_name': self.full_name,
            'role': self.role.value,
            'status': self.status.value,
            'preferences': self.preferences.to_dict(),
            'learning_settings': self.learning_settings.to_dict(),
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'email_verified_at': self.email_verified_at.isoformat() if self.email_verified_at else None,
            'total_study_time_seconds': self.total_study_time_seconds,
            'total_questions_answered': self.total_questions_answered,
            'current_streak_days': self.current_streak_days,
            'longest_streak_days': self.longest_streak_days,
            'achievement_points': self.achievement_points,
        })
        return data