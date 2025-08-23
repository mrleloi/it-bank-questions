"""Exception handlers for FastAPI."""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException

from domain.exceptions import (
    DomainException,
    EntityNotFoundException,
    DuplicateEntityException,
    BusinessRuleViolationException,
    InvalidStateTransitionException
)


async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail
            }
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation exceptions."""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"][1:]),
            "message": error["msg"],
            "type": error["type"]
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": errors
            }
        }
    )


async def domain_exception_handler(request: Request, exc: Exception):
    """Handle domain exceptions."""
    # Map domain exceptions to HTTP status codes
    status_code_map = {
        EntityNotFoundException: status.HTTP_404_NOT_FOUND,
        DuplicateEntityException: status.HTTP_409_CONFLICT,
        BusinessRuleViolationException: status.HTTP_400_BAD_REQUEST,
        InvalidStateTransitionException: status.HTTP_400_BAD_REQUEST,
    }

    if isinstance(exc, DomainException):
        status_code = status_code_map.get(
            type(exc),
            status.HTTP_400_BAD_REQUEST
        )

        return JSONResponse(
            status_code=status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details
                }
            }
        )

    # Log unexpected exceptions
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Unexpected error: {exc}", exc_info=True)

    # Return generic error for unexpected exceptions
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred"
            }
        }
    )