"""FastAPI dependencies."""

from functools import lru_cache
from typing import Optional, Annotated, AsyncGenerator
from uuid import UUID

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt.exceptions import InvalidTokenError

from shared.dependency_injection import Container
from domain.repositories import *
from domain.services import *
from application.config import ApplicationConfig
from application.dto.common import PaginationRequest

# Security
security = HTTPBearer()


@lru_cache()
def get_container() -> Container:
    """Get dependency injection container."""
    from infrastructure.container import create_container
    return create_container()


@lru_cache()
def get_config() -> ApplicationConfig:
    """Get application configuration."""
    return ApplicationConfig.from_env()


async def get_db_session(
        container: Container = Depends(get_container)
) -> AsyncGenerator:
    """Get database session."""
    async with container.db.session() as session:
        yield session


# Authentication dependencies
async def get_current_user_id(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        config: ApplicationConfig = Depends(get_config)
) -> UUID:
    """Get current user ID from JWT token."""
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            config.auth.secret_key,
            algorithms=[config.auth.algorithm]
        )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return UUID(user_id)

    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
        user_id: UUID = Depends(get_current_user_id),
        container: Container = Depends(get_container)
) -> 'User':
    """Get current user entity."""
    user_repo = container.user_repository()
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if not user.can_login():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is {user.status.value}"
        )

    return user


async def get_optional_user(
        request: Request,
        config: ApplicationConfig = Depends(get_config)
) -> Optional[UUID]:
    """Get optional user ID from JWT token."""
    authorization = request.headers.get("Authorization")
    if not authorization:
        return None

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            return None

        payload = jwt.decode(
            token,
            config.auth.secret_key,
            algorithms=[config.auth.algorithm]
        )

        user_id = payload.get("sub")
        return UUID(user_id) if user_id else None

    except (ValueError, InvalidTokenError):
        return None


# Pagination dependencies
async def get_pagination(
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        sort_order: str = "asc"
) -> PaginationRequest:
    """Get pagination parameters."""
    pagination = PaginationRequest(
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order
    )
    pagination.validate()
    return pagination


# Repository dependencies
def get_user_repository(
        container: Container = Depends(get_container)
) -> 'UserRepository':
    """Get user repository."""
    return container.user_repository()


def get_question_repository(
        container: Container = Depends(get_container)
) -> 'QuestionRepository':
    """Get question repository."""
    return container.question_repository()


def get_session_repository(
        container: Container = Depends(get_container)
) -> 'SessionRepository':
    """Get session repository."""
    return container.session_repository()


def get_progress_repository(
        container: Container = Depends(get_container)
) -> 'ProgressRepository':
    """Get progress repository."""
    return container.progress_repository()


# Service dependencies
def get_spaced_repetition_service(
        container: Container = Depends(get_container)
) -> 'SpacedRepetitionService':
    """Get spaced repetition service."""
    return container.spaced_repetition_service()


def get_learning_path_service(
        container: Container = Depends(get_container)
) -> 'LearningPathService':
    """Get learning path service."""
    return container.learning_path_service()


def get_achievement_service(
        container: Container = Depends(get_container)
) -> 'AchievementService':
    """Get achievement service."""
    return container.achievement_service()


def get_analytics_service(
        container: Container = Depends(get_container)
) -> 'AnalyticsService':
    """Get analytics service."""
    return container.analytics_service()


# Use case dependencies
def get_use_case(use_case_name: str):
    """Get use case by name."""

    def _get_use_case(container: Container = Depends(get_container)):
        return getattr(container, use_case_name)()

    return _get_use_case