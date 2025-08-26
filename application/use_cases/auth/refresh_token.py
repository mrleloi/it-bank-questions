"""Refresh token use case."""

import jwt
from datetime import datetime, timedelta
from typing import Tuple

from domain.repositories import UserRepository
from domain.exceptions import EntityNotFoundException, BusinessRuleViolationException
from application.dto.request import RefreshTokenRequest
from application.dto.response import AuthTokenResponse, UserResponse
from application.mappers import UserMapper
from application.config import AuthConfig


class RefreshTokenUseCase:
    """Use case for refreshing access tokens."""

    def __init__(
            self,
            user_repository: UserRepository,
            auth_config: AuthConfig
    ):
        self.user_repo = user_repository
        self.auth_config = auth_config

    async def execute(self, request: RefreshTokenRequest) -> AuthTokenResponse:
        """Refresh access token using refresh token."""
        # Validate request
        request.validate()

        # Decode refresh token
        try:
            payload = jwt.decode(
                request.refresh_token,
                self.auth_config.secret_key,
                algorithms=[self.auth_config.algorithm]
            )
        except jwt.ExpiredSignatureError:
            raise BusinessRuleViolationException("Refresh token has expired")
        except jwt.InvalidTokenError:
            raise BusinessRuleViolationException("Invalid refresh token")

        # Validate token type
        if payload.get('type') != 'refresh':
            raise BusinessRuleViolationException("Invalid token type")

        # Get user
        user_id = payload.get('sub')
        if not user_id:
            raise BusinessRuleViolationException("Invalid token payload")

        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise EntityNotFoundException("User not found")

        # Check if user can still login
        if not user.can_login():
            raise BusinessRuleViolationException(
                f"Account is {user.status.value}. Cannot refresh token."
            )

        # Generate new tokens
        access_token, new_refresh_token = self._generate_tokens(user_id)

        # Update last login
        user.update_login()
        await self.user_repo.save(user)

        # Return response
        return AuthTokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=self.auth_config.access_token_expire_minutes * 60,
            user=UserMapper.to_response_dto(user)
        )

    def _generate_tokens(self, user_id: str) -> Tuple[str, str]:
        """Generate new access and refresh tokens."""
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