"""User repository implementation."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime

from domain.entities import User, UserPreferences, LearningSettings
from domain.value_objects import UserRole, UserStatus, ReviewInterval
from domain.repositories import UserRepository
from infrastructure.persistence.models import UserModel, UserPreferencesModel
from .base import DjangoRepository


class DjangoUserRepository(DjangoRepository[User, UserModel], UserRepository):
    """Django implementation of UserRepository."""

    def __init__(self, cache_manager=None):
        super().__init__(UserModel, cache_manager)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        try:
            model = await UserModel.objects.select_related('preferences').aget(email=email)
            return self._to_entity(model)
        except UserModel.DoesNotExist:
            return None

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        try:
            model = await UserModel.objects.select_related('preferences').aget(username=username)
            return self._to_entity(model)
        except UserModel.DoesNotExist:
            return None

    async def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email."""
        return await UserModel.objects.filter(email=email).aexists()

    async def exists_by_username(self, username: str) -> bool:
        """Check if user exists by username."""
        return await UserModel.objects.filter(username=username).aexists()

    async def get_active_users(
            self,
            limit: Optional[int] = None,
            offset: Optional[int] = None
    ) -> List[User]:
        """Get active users."""
        queryset = UserModel.objects.filter(
            status='active',
            is_deleted=False
        ).select_related('preferences')

        if offset:
            queryset = queryset[offset:]
        if limit:
            queryset = queryset[:limit]

        models = [m async for m in queryset]
        return [self._to_entity(m) for m in models]

    async def get_users_by_role(
            self,
            role: str,
            limit: Optional[int] = None,
            offset: Optional[int] = None
    ) -> List[User]:
        """Get users by role."""
        queryset = UserModel.objects.filter(
            role=role,
            is_deleted=False
        ).select_related('preferences')

        if offset:
            queryset = queryset[offset:]
        if limit:
            queryset = queryset[:limit]

        models = [m async for m in queryset]
        return [self._to_entity(m) for m in models]

    async def update_last_login(self, user_id: UUID, timestamp: datetime) -> bool:
        """Update user's last login timestamp."""
        updated = await UserModel.objects.filter(id=user_id).aupdate(
            last_login_at=timestamp,
            last_activity_at=timestamp
        )

        # Invalidate cache
        if self.cache:
            await self.cache.delete(f"UserModel:{user_id}")

        return updated > 0

    async def search_users(
            self,
            query: str,
            limit: Optional[int] = None,
            offset: Optional[int] = None
    ) -> List[User]:
        """Search users by name, email, or username."""
        from django.db.models import Q

        queryset = UserModel.objects.filter(
            Q(email__icontains=query) |
            Q(username__icontains=query) |
            Q(full_name__icontains=query)
        ).filter(is_deleted=False).select_related('preferences')

        if offset:
            queryset = queryset[offset:]
        if limit:
            queryset = queryset[:limit]

        models = [m async for m in queryset]
        return [self._to_entity(m) for m in models]

    def _to_entity(self, model: UserModel) -> User:
        """Convert UserModel to User entity."""
        # Get preferences
        try:
            pref_model = model.preferences
            preferences = UserPreferences(
                theme=pref_model.theme,
                language=pref_model.language,
                timezone=pref_model.timezone,
                email_notifications=pref_model.email_notifications,
                daily_reminder=pref_model.daily_reminder,
                reminder_time=str(pref_model.reminder_time)
            )

            # Parse review settings
            review_config = pref_model.review_settings or {}
            review_interval = ReviewInterval(
                learning_steps=review_config.get('learning_steps', [1, 10]),
                graduating_interval=review_config.get('graduating_interval', 1),
                easy_interval=review_config.get('easy_interval', 4),
                starting_ease=review_config.get('starting_ease', 2.5),
                easy_bonus=review_config.get('easy_bonus', 1.3),
                interval_modifier=review_config.get('interval_modifier', 1.0),
                maximum_interval=review_config.get('maximum_interval', 36500),
                leech_threshold=review_config.get('leech_threshold', 8)
            )

            learning_settings = LearningSettings(
                daily_goal=pref_model.daily_goal,
                review_interval=review_interval,
                auto_play_audio=pref_model.auto_play_audio,
                show_timer=pref_model.show_timer,
                enable_hints=pref_model.enable_hints,
                difficulty_preference=pref_model.difficulty_preference
            )
        except UserPreferencesModel.DoesNotExist:
            preferences = UserPreferences()
            learning_settings = LearningSettings()

        user = User(
            id=model.id,
            email=model.email,
            username=model.username,
            full_name=model.full_name,
            role=UserRole(model.role),
            status=UserStatus(model.status),
            preferences=preferences,
            learning_settings=learning_settings,
            last_login_at=model.last_login_at,
            email_verified_at=model.email_verified_at,
            total_study_time_seconds=model.total_study_time_seconds,
            total_questions_answered=model.total_questions_answered,
            current_streak_days=model.current_streak_days,
            longest_streak_days=model.longest_streak_days,
            achievement_points=model.achievement_points,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

        # Set password hash directly (not through constructor)
        user.password_hash = model.password

        return user

    def _to_model(self, entity: User) -> UserModel:
        """Convert User entity to UserModel."""
        model = UserModel(
            id=entity.id,
            email=entity.email,
            username=entity.username,
            password=getattr(entity, 'password_hash', ''),
            full_name=entity.full_name,
            role=entity.role.value,
            status=entity.status.value,
            email_verified_at=entity.email_verified_at,
            last_login_at=entity.last_login_at,
            total_study_time_seconds=entity.total_study_time_seconds,
            total_questions_answered=entity.total_questions_answered,
            current_streak_days=entity.current_streak_days,
            longest_streak_days=entity.longest_streak_days,
            achievement_points=entity.achievement_points
        )

        return model