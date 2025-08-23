"""Email service interface."""

from abc import ABC, abstractmethod
from typing import Dict, Any


class EmailService(ABC):
    """Abstract email service."""

    @abstractmethod
    async def send_verification_email(
            self,
            email: str,
            username: str,
            token: str
    ) -> bool:
        """Send email verification."""
        pass

    @abstractmethod
    async def send_password_reset_email(
            self,
            email: str,
            username: str,
            token: str
    ) -> bool:
        """Send password reset email."""
        pass

    @abstractmethod
    async def send_achievement_email(
            self,
            email: str,
            achievement_name: str,
            points: int
    ) -> bool:
        """Send achievement notification email."""
        pass

    @abstractmethod
    async def send_daily_reminder(
            self,
            email: str,
            stats: Dict[str, Any]
    ) -> bool:
        """Send daily study reminder."""
        pass
