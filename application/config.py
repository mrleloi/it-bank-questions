"""Application configuration."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class AuthConfig:
    """Authentication configuration."""

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    password_reset_expire_hours: int = 24
    email_verification_expire_days: int = 7


@dataclass
class LearningConfig:
    """Learning configuration."""

    daily_new_cards_limit: int = 20
    daily_review_limit: int = 100
    session_timeout_minutes: int = 30
    min_session_questions: int = 5
    max_session_questions: int = 50
    default_time_limit_minutes: int = 30


@dataclass
class CacheConfig:
    """Cache configuration."""

    default_ttl: int = 3600  # 1 hour
    user_cache_ttl: int = 1800  # 30 minutes
    question_cache_ttl: int = 7200  # 2 hours
    progress_cache_ttl: int = 600  # 10 minutes


@dataclass
class ApplicationConfig:
    """Main application configuration."""

    auth: AuthConfig
    learning: LearningConfig
    cache: CacheConfig
    debug: bool = False

    @classmethod
    def from_env(cls) -> 'ApplicationConfig':
        """Create configuration from environment variables."""
        import os

        return cls(
            auth=AuthConfig(
                secret_key=os.getenv('SECRET_KEY', 'dev-secret-key'),
                access_token_expire_minutes=int(os.getenv('ACCESS_TOKEN_EXPIRE', '30')),
                refresh_token_expire_days=int(os.getenv('REFRESH_TOKEN_EXPIRE', '7'))
            ),
            learning=LearningConfig(
                daily_new_cards_limit=int(os.getenv('DAILY_NEW_CARDS', '20')),
                daily_review_limit=int(os.getenv('DAILY_REVIEW_LIMIT', '100'))
            ),
            cache=CacheConfig(
                default_ttl=int(os.getenv('CACHE_TTL', '3600'))
            ),
            debug=os.getenv('DEBUG', 'false').lower() == 'true'
        )
