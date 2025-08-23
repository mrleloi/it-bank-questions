"""Authentication-related request DTOs."""

from dataclasses import dataclass
from typing import Optional, Dict, Any
import re


@dataclass
class RegisterUserRequest:
    """User registration request."""

    email: str
    username: str
    password: str
    full_name: Optional[str] = None
    timezone: str = "UTC"
    language: str = "en"

    def validate(self) -> None:
        """Validate registration data."""
        # Email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, self.email):
            raise ValueError("Invalid email format")

        # Username validation
        if len(self.username) < 3 or len(self.username) > 50:
            raise ValueError("Username must be between 3 and 50 characters")

        if not self.username.replace('_', '').isalnum():
            raise ValueError("Username can only contain letters, numbers, and underscores")

        # Password validation
        if len(self.password) < 8:
            raise ValueError("Password must be at least 8 characters")

        if not any(c.isupper() for c in self.password):
            raise ValueError("Password must contain at least one uppercase letter")

        if not any(c.islower() for c in self.password):
            raise ValueError("Password must contain at least one lowercase letter")

        if not any(c.isdigit() for c in self.password):
            raise ValueError("Password must contain at least one digit")


@dataclass
class LoginRequest:
    """User login request."""

    username_or_email: str
    password: str
    remember_me: bool = False

    def validate(self) -> None:
        """Validate login data."""
        if not self.username_or_email:
            raise ValueError("Username or email is required")

        if not self.password:
            raise ValueError("Password is required")


@dataclass
class RefreshTokenRequest:
    """Token refresh request."""

    refresh_token: str

    def validate(self) -> None:
        """Validate refresh token."""
        if not self.refresh_token:
            raise ValueError("Refresh token is required")


@dataclass
class ResetPasswordRequest:
    """Password reset request."""

    email: str

    def validate(self) -> None:
        """Validate email."""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, self.email):
            raise ValueError("Invalid email format")


@dataclass
class ConfirmPasswordResetRequest:
    """Confirm password reset request."""

    token: str
    new_password: str

    def validate(self) -> None:
        """Validate reset data."""
        if not self.token:
            raise ValueError("Reset token is required")

        if len(self.new_password) < 8:
            raise ValueError("Password must be at least 8 characters")


@dataclass
class UpdateUserRequest:
    """Update user profile request."""

    full_name: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    learning_settings: Optional[Dict[str, Any]] = None

    def validate(self) -> None:
        """Validate update data."""
        if self.full_name is not None and len(self.full_name) > 255:
            raise ValueError("Full name too long")

        if self.language is not None and self.language not in ['en', 'vi', 'ja', 'ko', 'zh']:
            raise ValueError("Unsupported language")
