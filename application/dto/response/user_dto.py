"""User-related response DTOs."""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID


@dataclass
class UserResponse:
    """User response DTO."""

    id: UUID
    email: str
    username: str
    full_name: Optional[str]
    role: str
    status: str
    preferences: Dict[str, Any]
    learning_settings: Dict[str, Any]
    created_at: datetime
    last_login_at: Optional[datetime]
    email_verified: bool

    # Statistics
    total_study_time_seconds: int
    total_questions_answered: int
    current_streak_days: int
    achievement_points: int

    @classmethod
    def from_entity(cls, user: 'User') -> 'UserResponse':
        """Create from User entity."""
        return cls(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            role=user.role.value,
            status=user.status.value,
            preferences=user.preferences.to_dict(),
            learning_settings=user.learning_settings.to_dict(),
            created_at=user.created_at,
            last_login_at=user.last_login_at,
            email_verified=user.is_verified(),
            total_study_time_seconds=user.total_study_time_seconds,
            total_questions_answered=user.total_questions_answered,
            current_streak_days=user.current_streak_days,
            achievement_points=user.achievement_points
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': str(self.id),
            'email': self.email,
            'username': self.username,
            'full_name': self.full_name,
            'role': self.role,
            'status': self.status,
            'preferences': self.preferences,
            'learning_settings': self.learning_settings,
            'created_at': self.created_at.isoformat(),
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'email_verified': self.email_verified,
            'statistics': {
                'total_study_time_seconds': self.total_study_time_seconds,
                'total_questions_answered': self.total_questions_answered,
                'current_streak_days': self.current_streak_days,
                'achievement_points': self.achievement_points
            }
        }


@dataclass
class AuthTokenResponse:
    """Authentication token response."""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600  # seconds
    user: UserResponse = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        response = {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'token_type': self.token_type,
            'expires_in': self.expires_in
        }

        if self.user:
            response['user'] = self.user.to_dict()

        return response
