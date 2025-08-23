"""User-related value objects."""

from enum import Enum


class UserRole(str, Enum):
    """User roles in the system."""

    LEARNER = "learner"  # Regular learner
    MODERATOR = "moderator"  # Can moderate content
    ADMIN = "admin"  # Full system access
    GUEST = "guest"  # Limited access

    def has_permission(self, permission: str) -> bool:
        """Check if role has specific permission."""
        permissions = {
            UserRole.GUEST: {'view_content'},
            UserRole.LEARNER: {
                'view_content',
                'answer_questions',
                'view_progress',
                'create_notes',
            },
            UserRole.MODERATOR: {
                'view_content',
                'answer_questions',
                'view_progress',
                'create_notes',
                'moderate_content',
                'view_reports',
            },
            UserRole.ADMIN: {
                'view_content',
                'answer_questions',
                'view_progress',
                'create_notes',
                'moderate_content',
                'view_reports',
                'manage_users',
                'manage_content',
                'view_analytics',
                'system_settings',
            },
        }
        return permission in permissions.get(self, set())


class UserStatus(str, Enum):
    """User account status."""

    PENDING = "pending"  # Awaiting email verification
    ACTIVE = "active"  # Active account
    SUSPENDED = "suspended"  # Temporarily suspended
    BANNED = "banned"  # Permanently banned
    DELETED = "deleted"  # Soft deleted

    def can_login(self) -> bool:
        """Check if user with this status can login."""
        return self == UserStatus.ACTIVE

    def is_permanent(self) -> bool:
        """Check if this status is permanent."""
        return self in {UserStatus.BANNED, UserStatus.DELETED}
