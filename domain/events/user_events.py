"""User-related domain events."""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any
from uuid import UUID

from .base import UserDomainEvent


@dataclass
class UserRegisteredEvent(UserDomainEvent):
    """Event fired when a user registers."""
    
    email: str
    username: str
    full_name: str = None
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            'email': self.email,
            'username': self.username,
            'full_name': self.full_name
        }


@dataclass
class UserLoggedInEvent(UserDomainEvent):
    """Event fired when a user logs in."""
    
    login_method: str = "password"
    ip_address: str = None
    user_agent: str = None
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            'login_method': self.login_method,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent
        }


@dataclass
class UserLoggedOutEvent(UserDomainEvent):
    """Event fired when a user logs out."""
    
    session_duration_seconds: int = 0
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            'session_duration_seconds': self.session_duration_seconds
        }


@dataclass
class UserEmailVerifiedEvent(UserDomainEvent):
    """Event fired when a user's email is verified."""
    
    email: str
    verified_at: datetime
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            'email': self.email,
            'verified_at': self.verified_at.isoformat()
        }


@dataclass
class UserPasswordResetEvent(UserDomainEvent):
    """Event fired when a user resets their password."""
    
    email: str
    reset_method: str = "email"
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            'email': self.email,
            'reset_method': self.reset_method
        }


@dataclass
class UserProfileUpdatedEvent(UserDomainEvent):
    """Event fired when a user updates their profile."""
    
    updated_fields: list
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            'updated_fields': self.updated_fields
        }


@dataclass
class UserPreferencesUpdatedEvent(UserDomainEvent):
    """Event fired when a user updates their preferences."""
    
    updated_preferences: Dict[str, Any]
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            'updated_preferences': self.updated_preferences
        }


@dataclass
class UserSuspendedEvent(UserDomainEvent):
    """Event fired when a user account is suspended."""
    
    reason: str
    suspended_by: UUID = None
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            'reason': self.reason,
            'suspended_by': str(self.suspended_by) if self.suspended_by else None
        }


@dataclass
class UserActivatedEvent(UserDomainEvent):
    """Event fired when a user account is activated."""
    
    activated_by: UUID = None
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            'activated_by': str(self.activated_by) if self.activated_by else None
        }


@dataclass
class UserDeletedEvent(UserDomainEvent):
    """Event fired when a user deletes their account."""
    
    deletion_reason: str = None
    data_retention_days: int = 30
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            'deletion_reason': self.deletion_reason,
            'data_retention_days': self.data_retention_days
        }