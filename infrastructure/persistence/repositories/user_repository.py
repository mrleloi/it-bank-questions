from typing import Optional, List
from uuid import UUID
from datetime import datetime
from asgiref.sync import sync_to_async

from domain.entities import User, UserPreferences, LearningSettings
from domain.value_objects import UserRole, UserStatus, ReviewInterval
from domain.repositories import UserRepository
from infrastructure.persistence.models import UserModel, UserPreferencesModel
from .base import DjangoRepository


class DjangoUserRepository(DjangoRepository[User, UserModel], UserRepository):
    """Django implementation of UserRepository with proper async/sync handling."""

    def __init__(self, cache_manager=None):
        super().__init__(UserModel, cache_manager)

    def _apply_select_related(self, queryset):
        """Apply select_related for User model relationships."""
        return queryset.select_related('preferences')

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email with proper async handling."""
        model = await self._get_user_by_email(email)
        if not model:
            return None
        return await sync_to_async(self._to_entity)(model)

    @sync_to_async
    def _get_user_by_email(self, email: str) -> Optional[UserModel]:
        """Get user model by email in sync context."""
        try:
            return UserModel.objects.select_related('preferences').get(email=email)
        except UserModel.DoesNotExist:
            return None

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username with proper async handling."""
        model = await self._get_user_by_username(username)
        if not model:
            return None
        return await sync_to_async(self._to_entity)(model)

    @sync_to_async
    def _get_user_by_username(self, username: str) -> Optional[UserModel]:
        """Get user model by username in sync context."""
        try:
            return UserModel.objects.select_related('preferences').get(username=username)
        except UserModel.DoesNotExist:
            return None

    async def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email."""
        return await sync_to_async(
            UserModel.objects.filter(email=email).exists
        )()

    async def exists_by_username(self, username: str) -> bool:
        """Check if user exists by username."""
        return await sync_to_async(
            UserModel.objects.filter(username=username).exists
        )()

    async def get_active_users(
            self,
            limit: Optional[int] = None,
            offset: Optional[int] = None
    ) -> List[User]:
        """Get active users."""
        models = await self._get_active_user_models(limit, offset)
        entities = []
        for model in models:
            entity = await sync_to_async(self._to_entity)(model)
            entities.append(entity)
        return entities

    @sync_to_async
    def _get_active_user_models(
            self,
            limit: Optional[int],
            offset: Optional[int]
    ) -> List[UserModel]:
        """Get active user models in sync context."""
        queryset = UserModel.objects.filter(
            status='active',
            is_deleted=False
        ).select_related('preferences')

        if offset:
            queryset = queryset[offset:]
        if limit:
            queryset = queryset[:limit]

        return list(queryset)

    async def get_users_by_role(
            self,
            role: str,
            limit: Optional[int] = None,
            offset: Optional[int] = None
    ) -> List[User]:
        """Get users by role."""
        models = await self._get_users_by_role_models(role, limit, offset)
        entities = []
        for model in models:
            entity = await sync_to_async(self._to_entity)(model)
            entities.append(entity)
        return entities

    @sync_to_async
    def _get_users_by_role_models(
            self,
            role: str,
            limit: Optional[int],
            offset: Optional[int]
    ) -> List[UserModel]:
        """Get users by role in sync context."""
        queryset = UserModel.objects.filter(
            role=role,
            is_deleted=False
        ).select_related('preferences')

        if offset:
            queryset = queryset[offset:]
        if limit:
            queryset = queryset[:limit]

        return list(queryset)

    async def update_last_login(self, user_id: UUID, timestamp: datetime) -> bool:
        """Update user's last login timestamp."""
        result = await self._update_last_login_sync(user_id, timestamp)

        # Invalidate cache
        if self.cache:
            await self.cache.delete(f"UserModel:{user_id}")

        return result

    @sync_to_async
    def _update_last_login_sync(self, user_id: UUID, timestamp: datetime) -> bool:
        """Update last login in sync context."""
        updated = UserModel.objects.filter(id=user_id).update(
            last_login_at=timestamp,
            last_activity_at=timestamp
        )
        return updated > 0

    async def search_users(
            self,
            query: str,
            limit: Optional[int] = None,
            offset: Optional[int] = None
    ) -> List[User]:
        """Search users by name, email, or username."""
        models = await self._search_user_models(query, limit, offset)
        entities = []
        for model in models:
            entity = await sync_to_async(self._to_entity)(model)
            entities.append(entity)
        return entities

    @sync_to_async
    def _search_user_models(
            self,
            query: str,
            limit: Optional[int],
            offset: Optional[int]
    ) -> List[UserModel]:
        """Search users in sync context."""
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

        return list(queryset)

    def _to_entity(self, model: UserModel, load_relationship: bool = True) -> User:
        """Convert UserModel to User entity.
        This method runs in SYNC context, so it's safe to access relationships."""

        # Access preferences - safe in sync context
        preferences = None
        learning_settings = None

        try:
            # This is now safe because we're in sync context
            if hasattr(model, 'preferences'):
                pref_model = model.preferences

                preferences = UserPreferences(
                    theme=pref_model.theme,
                    language=pref_model.language,
                    timezone=pref_model.timezone,
                    email_notifications=pref_model.email_notifications,
                    daily_reminder=pref_model.daily_reminder,
                    reminder_time=str(pref_model.reminder_time) if pref_model.reminder_time else '09:00'
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
            # Use defaults if preferences don't exist
            preferences = UserPreferences()
            learning_settings = LearningSettings()

        # If preferences is still None, use defaults
        if preferences is None:
            preferences = UserPreferences()
        if learning_settings is None:
            learning_settings = LearningSettings()

        # Create user entity
        user = User(
            id=model.id,
            email=model.email,
            username=model.username,
            full_name=model.full_name or '',
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
        if hasattr(model, 'password'):
            user.password_hash = model.password

        return user

    def _to_model(self, entity: User) -> UserModel:
        """Convert User entity to UserModel.
        This method runs in SYNC context."""

        # Create or get the model
        if entity.id:
            try:
                model = UserModel.objects.get(id=entity.id)
            except UserModel.DoesNotExist:
                model = UserModel(id=entity.id)
        else:
            model = UserModel()

        # Update fields
        model.email = entity.email
        model.username = entity.username
        model.full_name = entity.full_name
        model.role = entity.role.value
        model.status = entity.status.value
        model.email_verified_at = entity.email_verified_at
        model.last_login_at = entity.last_login_at
        model.total_study_time_seconds = entity.total_study_time_seconds
        model.total_questions_answered = entity.total_questions_answered
        model.current_streak_days = entity.current_streak_days
        model.longest_streak_days = entity.longest_streak_days
        model.achievement_points = entity.achievement_points

        # Handle password
        if hasattr(entity, 'password_hash') and entity.password_hash:
            model.password = entity.password_hash

        return model

    def _update_model_from_entity(self, model: UserModel, entity: User) -> UserModel:
        """Update model from entity in sync context."""
        model.email = entity.email
        model.username = entity.username
        model.full_name = entity.full_name
        model.role = entity.role.value
        model.status = entity.status.value
        model.email_verified_at = entity.email_verified_at
        model.last_login_at = entity.last_login_at
        model.total_study_time_seconds = entity.total_study_time_seconds
        model.total_questions_answered = entity.total_questions_answered
        model.current_streak_days = entity.current_streak_days
        model.longest_streak_days = entity.longest_streak_days
        model.achievement_points = entity.achievement_points

        # Handle password if changed
        if hasattr(entity, 'password_hash') and entity.password_hash:
            model.password = entity.password_hash

        # Update preferences if they exist
        if entity.preferences:
            try:
                prefs = model.preferences
            except UserPreferencesModel.DoesNotExist:
                prefs = UserPreferencesModel(user=model)

            prefs.theme = entity.preferences.theme
            prefs.language = entity.preferences.language
            prefs.timezone = entity.preferences.timezone
            prefs.email_notifications = entity.preferences.email_notifications
            prefs.daily_reminder = entity.preferences.daily_reminder

            if entity.preferences.reminder_time:
                prefs.reminder_time = entity.preferences.reminder_time

            # Update learning settings
            if entity.learning_settings:
                prefs.daily_goal = entity.learning_settings.daily_goal
                prefs.auto_play_audio = entity.learning_settings.auto_play_audio
                prefs.show_timer = entity.learning_settings.show_timer
                prefs.enable_hints = entity.learning_settings.enable_hints
                prefs.difficulty_preference = entity.learning_settings.difficulty_preference

                # Update review settings
                if entity.learning_settings.review_interval:
                    review_interval = entity.learning_settings.review_interval
                    prefs.review_settings = {
                        'learning_steps': review_interval.learning_steps,
                        'graduating_interval': review_interval.graduating_interval,
                        'easy_interval': review_interval.easy_interval,
                        'starting_ease': review_interval.starting_ease,
                        'easy_bonus': review_interval.easy_bonus,
                        'interval_modifier': review_interval.interval_modifier,
                        'maximum_interval': review_interval.maximum_interval,
                        'leech_threshold': review_interval.leech_threshold
                    }

            prefs.save()

        return model