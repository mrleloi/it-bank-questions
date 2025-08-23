"""User management endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from application.use_cases.users import (
    GetUserProfileUseCase,
    UpdateUserProfileUseCase,
    UpdateUserSettingsUseCase,
    DeleteUserAccountUseCase
)
from application.dto.request import UpdateUserRequest
from application.dto.response import UserResponse
from ..dependencies import get_current_user_id, get_current_user, get_use_case

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
        user=Depends(get_current_user)
):
    """Get current user profile."""
    from application.mappers import UserMapper
    return UserMapper.to_response_dto(user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_profile(
        user_id: UUID,
        use_case: GetUserProfileUseCase = Depends(get_use_case("get_user_profile_use_case"))
):
    """Get user profile by ID."""
    return await use_case.execute(user_id)


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
        request: UpdateUserRequest,
        user_id: UUID = Depends(get_current_user_id),
        use_case: UpdateUserProfileUseCase = Depends(get_use_case("update_user_profile_use_case"))
):
    """Update current user profile."""
    return await use_case.execute(user_id, request)


@router.put("/me/settings")
async def update_user_settings(
        settings: dict,
        user_id: UUID = Depends(get_current_user_id),
        use_case: UpdateUserSettingsUseCase = Depends(get_use_case("update_user_settings_use_case"))
):
    """Update user settings."""
    return await use_case.execute(user_id, settings)


@router.delete("/me")
async def delete_account(
        confirmation: str = Query(..., regex="^DELETE$"),
        user_id: UUID = Depends(get_current_user_id),
        use_case: DeleteUserAccountUseCase = Depends(get_use_case("delete_user_account_use_case"))
):
    """Delete user account (requires confirmation)."""
    if confirmation != "DELETE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid confirmation"
        )

    await use_case.execute(user_id)
    return {"message": "Account deleted successfully"}