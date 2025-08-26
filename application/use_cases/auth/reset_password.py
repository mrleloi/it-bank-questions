"""Reset password use case."""

import bcrypt
import jwt
from datetime import datetime, timedelta
from uuid import uuid4

from domain.repositories import UserRepository
from domain.exceptions import EntityNotFoundException, BusinessRuleViolationException
from application.dto.request import ResetPasswordRequest, ConfirmPasswordResetRequest
from application.services import EmailService
from application.config import AuthConfig


class ResetPasswordUseCase:
    """Use case for password reset functionality."""

    def __init__(
            self,
            user_repository: UserRepository,
            email_service: EmailService,
            auth_config: AuthConfig
    ):
        self.user_repo = user_repository
        self.email_service = email_service
        self.auth_config = auth_config

    async def execute(self, request: ResetPasswordRequest) -> None:
        """Request password reset - send reset email."""
        # Validate request
        request.validate()

        # Find user by email
        user = await self.user_repo.get_by_email(request.email)
        if not user:
            # Don't reveal if email exists for security
            # but still return success to user
            return

        # Check if user can reset password
        if not user.can_login():
            # Don't send email to suspended/banned accounts
            return

        # Generate reset token
        reset_token = self._generate_reset_token(user.id)

        # Send reset email
        await self.email_service.send_password_reset_email(
            email=user.email,
            username=user.username,
            token=reset_token
        )

    async def confirm_reset(
            self, 
            request: ConfirmPasswordResetRequest
    ) -> None:
        """Confirm password reset with token and set new password."""
        # Validate request
        request.validate()

        # Decode reset token
        try:
            payload = jwt.decode(
                request.token,
                self.auth_config.secret_key,
                algorithms=[self.auth_config.algorithm]
            )
        except jwt.ExpiredSignatureError:
            raise BusinessRuleViolationException("Reset token has expired")
        except jwt.InvalidTokenError:
            raise BusinessRuleViolationException("Invalid reset token")

        # Validate token type and purpose
        if payload.get('type') != 'password_reset':
            raise BusinessRuleViolationException("Invalid token type")

        # Get user
        user_id = payload.get('sub')
        if not user_id:
            raise BusinessRuleViolationException("Invalid token payload")

        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise EntityNotFoundException("User not found")

        # Check if user can reset password
        if not user.can_login():
            raise BusinessRuleViolationException(
                f"Account is {user.status.value}. Cannot reset password."
            )

        # Hash new password
        new_password_hash = self._hash_password(request.new_password)

        # Update user password
        user.password_hash = new_password_hash
        user.update_timestamp()

        # Save user
        await self.user_repo.save(user)

    def _generate_reset_token(self, user_id: str) -> str:
        """Generate password reset token."""
        payload = {
            'sub': str(user_id),
            'type': 'password_reset',
            'exp': datetime.utcnow() + timedelta(
                hours=self.auth_config.password_reset_expire_hours
            ),
            'iat': datetime.utcnow(),
            'jti': str(uuid4())  # Unique token ID
        }

        return jwt.encode(
            payload,
            self.auth_config.secret_key,
            algorithm=self.auth_config.algorithm
        )

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')