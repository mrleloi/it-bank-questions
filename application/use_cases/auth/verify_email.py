"""Verify email use case."""

import jwt
from datetime import datetime

from domain.repositories import UserRepository
from domain.exceptions import EntityNotFoundException, BusinessRuleViolationException
from domain.events import UserEmailVerifiedEvent
from application.services import EventBus
from application.config import AuthConfig


class VerifyEmailUseCase:
    """Use case for email verification."""

    def __init__(
            self,
            user_repository: UserRepository,
            event_bus: EventBus,
            auth_config: AuthConfig
    ):
        self.user_repo = user_repository
        self.event_bus = event_bus
        self.auth_config = auth_config

    async def execute(self, token: str) -> None:
        """Verify email using verification token."""
        if not token:
            raise BusinessRuleViolationException("Verification token is required")

        # Decode verification token
        try:
            payload = jwt.decode(
                token,
                self.auth_config.secret_key,
                algorithms=[self.auth_config.algorithm]
            )
        except jwt.ExpiredSignatureError:
            raise BusinessRuleViolationException("Verification token has expired")
        except jwt.InvalidTokenError:
            raise BusinessRuleViolationException("Invalid verification token")

        # Validate token type
        if payload.get('type') != 'email_verification':
            raise BusinessRuleViolationException("Invalid token type")

        # Get user
        user_id = payload.get('sub')
        if not user_id:
            raise BusinessRuleViolationException("Invalid token payload")

        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise EntityNotFoundException("User not found")

        # Check if email already verified
        if user.is_verified():
            # Email already verified, nothing to do
            return

        # Verify email
        user.verify_email()

        # Save user
        await self.user_repo.save(user)

        # Publish domain event
        event = UserEmailVerifiedEvent(
            user_id=user.id,
            email=user.email,
            verified_at=datetime.now()
        )
        await self.event_bus.publish(event)

    async def resend_verification(self, email: str) -> None:
        """Resend verification email."""
        # Find user by email
        user = await self.user_repo.get_by_email(email)
        if not user:
            # Don't reveal if email exists
            return

        # Check if already verified
        if user.is_verified():
            return

        # Generate new verification token
        verification_token = self._generate_verification_token(user.id)

        # Send verification email (would need EmailService)
        # This would be implemented similar to registration
        pass

    def _generate_verification_token(self, user_id: str) -> str:
        """Generate email verification token."""
        from datetime import timedelta
        from uuid import uuid4

        payload = {
            'sub': str(user_id),
            'type': 'email_verification',
            'exp': datetime.utcnow() + timedelta(
                days=self.auth_config.email_verification_expire_days
            ),
            'iat': datetime.utcnow(),
            'jti': str(uuid4())
        }

        return jwt.encode(
            payload,
            self.auth_config.secret_key,
            algorithm=self.auth_config.algorithm
        )