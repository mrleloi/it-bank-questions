"""Authentication endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm

from application.use_cases.auth import (
    RegisterUserUseCase,
    AuthenticateUserUseCase,
    RefreshTokenUseCase,
    VerifyEmailUseCase,
    ResetPasswordUseCase
)
from application.dto.request import (
    RegisterUserRequest,
    LoginRequest,
    RefreshTokenRequest,
    ResetPasswordRequest,
    ConfirmPasswordResetRequest
)
from application.dto.response import AuthTokenResponse, UserResponse
from ..dependencies import get_use_case

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
        request: RegisterUserRequest,
        use_case: RegisterUserUseCase = Depends(get_use_case("register_user_use_case"))
):
    """Register a new user."""
    try:
        return await use_case.execute(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=AuthTokenResponse)
async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        use_case: AuthenticateUserUseCase = Depends(get_use_case("authenticate_user_use_case"))
):
    """Login with username/email and password."""
    request = LoginRequest(
        username_or_email=form_data.username,
        password=form_data.password
    )

    try:
        return await use_case.execute(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )


@router.post("/refresh", response_model=AuthTokenResponse)
async def refresh_token(
        request: RefreshTokenRequest,
        use_case: RefreshTokenUseCase = Depends(get_use_case("refresh_token_use_case"))
):
    """Refresh access token using refresh token."""
    try:
        return await use_case.execute(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.post("/verify-email/{token}")
async def verify_email(
        token: str,
        use_case: VerifyEmailUseCase = Depends(get_use_case("verify_email_use_case"))
):
    """Verify email address using token."""
    try:
        await use_case.execute(token)
        return {"message": "Email verified successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/reset-password")
async def request_password_reset(
        request: ResetPasswordRequest,
        use_case: ResetPasswordUseCase = Depends(get_use_case("reset_password_use_case"))
):
    """Request password reset email."""
    try:
        await use_case.execute(request)
        return {"message": "Password reset email sent"}
    except Exception as e:
        # Don't reveal if email exists
        return {"message": "Password reset email sent"}


@router.post("/reset-password/confirm")
async def confirm_password_reset(
        request: ConfirmPasswordResetRequest,
        use_case: ResetPasswordUseCase = Depends(get_use_case("reset_password_use_case"))
):
    """Confirm password reset with token."""
    try:
        await use_case.confirm_reset(request)
        return {"message": "Password reset successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
