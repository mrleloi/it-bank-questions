"""Notification service interface."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from uuid import UUID
from enum import Enum


class NotificationType(str, Enum):
    """Types of notifications."""
    
    ACHIEVEMENT = "achievement"
    DAILY_REMINDER = "daily_reminder"  
    STREAK_MILESTONE = "streak_milestone"
    SESSION_COMPLETED = "session_completed"
    FACET_MASTERED = "facet_mastered"
    REVIEW_DUE = "review_due"
    WEEKLY_SUMMARY = "weekly_summary"
    SYSTEM_ANNOUNCEMENT = "system_announcement"


class NotificationChannel(str, Enum):
    """Notification delivery channels."""
    
    EMAIL = "email"
    PUSH = "push"
    IN_APP = "in_app"
    SMS = "sms"  # Future
    SLACK = "slack"  # Future


class NotificationService(ABC):
    """Abstract notification service."""

    @abstractmethod
    async def send_notification(
            self,
            user_id: UUID,
            notification_type: NotificationType,
            title: str,
            message: str,
            data: Optional[Dict[str, Any]] = None,
            channels: Optional[List[NotificationChannel]] = None
    ) -> bool:
        """Send notification to user."""
        pass

    @abstractmethod
    async def send_bulk_notification(
            self,
            user_ids: List[UUID],
            notification_type: NotificationType,
            title: str,
            message: str,
            data: Optional[Dict[str, Any]] = None,
            channels: Optional[List[NotificationChannel]] = None
    ) -> Dict[UUID, bool]:
        """Send notification to multiple users."""
        pass

    @abstractmethod
    async def schedule_notification(
            self,
            user_id: UUID,
            notification_type: NotificationType,
            title: str,
            message: str,
            scheduled_at: str,  # ISO datetime
            data: Optional[Dict[str, Any]] = None,
            channels: Optional[List[NotificationChannel]] = None
    ) -> str:
        """Schedule notification for later delivery."""
        pass

    @abstractmethod
    async def cancel_scheduled_notification(
            self,
            notification_id: str
    ) -> bool:
        """Cancel a scheduled notification."""
        pass

    @abstractmethod
    async def get_user_preferences(
            self,
            user_id: UUID
    ) -> Dict[str, Any]:
        """Get user's notification preferences."""
        pass

    @abstractmethod
    async def update_user_preferences(
            self,
            user_id: UUID,
            preferences: Dict[str, Any]
    ) -> bool:
        """Update user's notification preferences."""
        pass