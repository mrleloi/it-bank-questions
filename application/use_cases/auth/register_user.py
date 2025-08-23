"""Register user use case."""

import bcrypt
from typing import Optional
from uuid import uuid4

from domain.entities import User
from domain.repositories import UserRepository
from domain.exceptions import DuplicateEntityException
from domain.events import UserRegisteredEvent
from application.dto.request import RegisterUserRequest
from application.dto.response import UserResponse
from application.mappers import UserMapper
from application.services import EmailService, EventBus


class RegisterUserUseCase:
    """Use case for user registration."""

    def __init__(
            self,
            user_repository: UserRepository,
            email_service: EmailService,
            event_bus: EventBus
    ):
        self.user_repo = user_repository
        self.email_service = email_service
        self.event_bus = event_bus

    async def execute(self, request: RegisterUserRequest) -> UserResponse:
        """Register a new user."""
        # Validate request
        request.validate()

        # Check if user already exists
        if await self.user_repo.exists_by_email(request.email):
            raise DuplicateEntityException(
                f"User with email {request.email} already exists"
            )

        if await self.user_repo.exists_by_username(request.username):
            raise DuplicateEntityException(
                f"Username {request.username} is already taken"
            )

        # Create user entity
        user = UserMapper.from_register_request(request)

        # Hash password (would normally be in infrastructure layer)
        user.password_hash = self._hash_password(request.password)

        # Validate entity
        user.validate()

        # Save user
        saved_user = await self.user_repo.save(user)

        # Send verification email
        verification_token = str(uuid4())
        await self.email_service.send_verification_email(
            saved_user.email,
            saved_user.username,
            verification_token
        )

        # Publish domain event
        event = UserRegisteredEvent(
            user_id=saved_user.id,
            email=saved_user.email,
            username=saved_user.username
        )
        await self.event_bus.publish(event)

        # Return response
        return UserMapper.to_response_dto(saved_user)

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')