"""Authenticate user use case."""

import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Tuple

from domain.repositories import UserRepository
from domain.exceptions import EntityNotFoundException, BusinessRuleViolationException
from domain.events import UserLoggedInEvent
from application.dto.request import LoginRequest
from application.dto.response import AuthTokenResponse, UserResponse
from application.mappers import UserMapper
from application.services import EventBus
from application.config import AuthConfig


class AuthenticateUserUseCase:
    """Use case for user authentication."""

    def __init__(
            self,
            user_repository: UserRepository,
            event_bus: EventBus,
            auth_config: AuthConfig
    ):
        self.user_repo = user_repository
        self.event_bus = event_bus
        self.auth_config = auth_config

    async def execute(self, request: LoginRequest) -> AuthTokenResponse:
        """Authenticate user and return tokens."""
        # Validate request
        request.validate()

        # Find user by email or username
        user = None
        if '@' in request.username_or_email:
            user = await self.user_repo.get_by_email(request.username_or_email)
        else:
            user = await self.user_repo.get_by_username(request.username_or_email)

        if not user:
            raise EntityNotFoundException("Invalid credentials")

        # Verify password
        if not self._verify_password(request.password, user.password_hash):
            raise BusinessRuleViolationException("Invalid credentials")

        # Check if user can login
        if not user.can_login():
            raise BusinessRuleViolationException(
                f"Account is {user.status.value}. Please contact support."
            )

        # Generate tokens
        access_token, refresh_token = self._generate_tokens(user.id)

        # Update last login
        user.update_login()
        await self.user_repo.save(user)

        # Publish login event
        event = UserLoggedInEvent(user_id=user.id)
        await self.event_bus.publish(event)

        # Return response
        return AuthTokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.auth_config.access_token_expire_minutes * 60,
            user=UserMapper.to_response_dto(user)
        )

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password using bcrypt."""
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )

    def _generate_tokens(self, user_id: str) -> Tuple[str, str]:
        """Generate access and refresh tokens."""
        # Access token
        access_payload = {
            'sub': str(user_id),
            'type': 'access',
            'exp': datetime.utcnow() + timedelta(
                minutes=self.auth_config.access_token_expire_minutes
            ),
            'iat': datetime.utcnow()
        }
        access_token = jwt.encode(
            access_payload,
            self.auth_config.secret_key,
            algorithm=self.auth_config.algorithm
        )

        # Refresh token
        refresh_payload = {
            'sub': str(user_id),
            'type': 'refresh',
            'exp': datetime.utcnow() + timedelta(
                days=self.auth_config.refresh_token_expire_days
            ),
            'iat': datetime.utcnow()
        }
        refresh_token = jwt.encode(
            refresh_payload,
            self.auth_config.secret_key,
            algorithm=self.auth_config.algorithm
        )

        return access_token, refresh_token