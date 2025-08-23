"""FastAPI main application."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.middleware.sessions import SessionMiddleware

from .dependencies import get_container
from .middleware import (
    RateLimitMiddleware,
    LoggingMiddleware,
    RequestIdMiddleware
)
from .exception_handlers import (
    http_exception_handler,
    validation_exception_handler,
    domain_exception_handler
)
from .v1 import router as v1_router
from application.config import ApplicationConfig


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager."""
    # Startup
    container = get_container()
    await container.init_resources()

    # Store container in app state
    app.state.container = container
    app.state.config = ApplicationConfig.from_env()

    print("✅ Application started successfully")

    yield

    # Shutdown
    await container.shutdown_resources()
    print("👋 Application shutdown complete")


def create_app() -> FastAPI:
    """Create FastAPI application."""
    app = FastAPI(
        title="Learning Platform API",
        description="Adaptive learning platform with spaced repetition",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:3001",
            "https://learning-platform.com"
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Total-Count"]
    )

    # Add security middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Configure for production
    )

    # Add session middleware
    app.add_middleware(
        SessionMiddleware,
        secret_key=ApplicationConfig.from_env().auth.secret_key
    )

    # Add custom middleware
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RateLimitMiddleware)

    # Register exception handlers
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, domain_exception_handler)

    # Include routers
    app.include_router(v1_router, prefix="/api/v1")

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "version": "1.0.0"
        }

    return app


app = create_app()