"""Achievement endpoints."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from application.dto.response import AchievementResponse
from ..dependencies import get_current_user_id, get_use_case

router = APIRouter()


@router.get("/", response_model=List[AchievementResponse])
async def list_achievements(
    unlocked_only: bool = Query(False),
    user_id: UUID = Depends(get_current_user_id),
    use_case = Depends(get_use_case("list_achievements_use_case"))
):
    """List all achievements."""
    return await use_case.execute(user_id, unlocked_only)


@router.get("/unlocked", response_model=List[AchievementResponse])
async def get_unlocked_achievements(
    user_id: UUID = Depends(get_current_user_id),
    use_case = Depends(get_use_case("get_unlocked_achievements_use_case"))
):
    """Get user's unlocked achievements."""
    return await use_case.execute(user_id)


@router.get("/progress")
async def get_achievement_progress(
    user_id: UUID = Depends(get_current_user_id),
    use_case = Depends(get_use_case("get_achievement_progress_use_case"))
):
    """Get progress towards locked achievements."""
    return await use_case.execute(user_id)


@router.post("/check")
async def check_achievements(
    user_id: UUID = Depends(get_current_user_id),
    use_case = Depends(get_use_case("check_achievements_use_case"))
):
    """Manually trigger achievement check."""
    return await use_case.execute(user_id)
