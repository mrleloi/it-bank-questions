"""User mapper."""

from typing import Optional
from uuid import UUID

from domain.entities import User, UserPreferences, LearningSettings
from domain.value_objects import UserRole, UserStatus, ReviewInterval
from application.dto.response import UserResponse
from application.dto.request import RegisterUserRequest, UpdateUserRequest
from .base import Mapper


class UserMapper:
    """Mapper for User entity and DTOs."""

    @staticmethod
    def to_response_dto(user: User) -> UserResponse:
        """Convert User entity to response DTO."""
        return UserResponse(
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

    @staticmethod
    def from_register_request(request: RegisterUserRequest) -> User:
        """Create User entity from registration request."""
        preferences = UserPreferences(
            language=request.language,
            timezone=request.timezone
        )

        return User(
            email=request.email,
            username=request.username,
            full_name=request.full_name,
            role=UserRole.LEARNER,
            status=UserStatus.PENDING,
            preferences=preferences,
            learning_settings=LearningSettings()
        )

    @staticmethod
    def update_from_request(user: User, request: UpdateUserRequest) -> User:
        """Update User entity from update request."""
        if request.full_name is not None:
            user.full_name = request.full_name

        if request.timezone is not None:
            user.preferences.timezone = request.timezone

        if request.language is not None:
            user.preferences.language = request.language

        if request.preferences:
            # Update specific preference fields
            for key, value in request.preferences.items():
                if hasattr(user.preferences, key):
                    setattr(user.preferences, key, value)

        if request.learning_settings:
            # Update learning settings
            for key, value in request.learning_settings.items():
                if hasattr(user.learning_settings, key):
                    setattr(user.learning_settings, key, value)

        user.update_timestamp()
        return user
