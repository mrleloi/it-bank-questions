"""Domain-specific exceptions."""

from typing import Optional, Dict, Any


class DomainException(Exception):
    """Base exception for all domain errors."""

    def __init__(
            self,
            message: str,
            code: Optional[str] = None,
            details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}


class EntityNotFoundException(DomainException):
    """Raised when an entity is not found."""
    pass


class EntityValidationException(DomainException):
    """Raised when entity validation fails."""
    pass


class BusinessRuleViolationException(DomainException):
    """Raised when a business rule is violated."""
    pass


class InvalidStateTransitionException(DomainException):
    """Raised when an invalid state transition is attempted."""
    pass


class DuplicateEntityException(DomainException):
    """Raised when attempting to create a duplicate entity."""
    pass


class InsufficientPermissionsException(DomainException):
    """Raised when user lacks required permissions."""
    pass


class QuestionNotFoundException(EntityNotFoundException):
    """Raised when a question is not found."""
    pass


class UserNotFoundException(EntityNotFoundException):
    """Raised when a user is not found."""
    pass


class InvalidAnswerException(BusinessRuleViolationException):
    """Raised when an answer is invalid."""
    pass


class SessionExpiredException(BusinessRuleViolationException):
    """Raised when a learning session has expired."""
    pass