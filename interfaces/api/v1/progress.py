"""Progress tracking endpoints."""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from application.use_cases.progress import (
    GetUserProgressUseCase,
    GetFacetProgressUseCase,
    GetLeaderboardUseCase
)
from application.dto.response import (
    UserProgressResponse,
    FacetProgressResponse,
    LeaderboardEntryResponse
)
from ..dependencies import get_current_user_id, get_use_case

router = APIRouter()


@router.get("/user", response_model=UserProgressResponse)
async def get_user_progress(
    user_id: UUID = Depends(get_current_user_id),
    use_case: GetUserProgressUseCase = Depends(get_use_case("get_user_progress_use_case"))
):
    """Get overall user progress."""
    return await use_case.execute(user_id)


@router.get("/facet/{facet_id}", response_model=FacetProgressResponse)
async def get_facet_progress(
    facet_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    use_case: GetFacetProgressUseCase = Depends(get_use_case("get_facet_progress_use_case"))
):
    """Get progress for a specific facet."""
    return await use_case.execute(user_id, facet_id)


@router.get("/facets", response_model=List[FacetProgressResponse])
async def list_facet_progress(
    mastery_level: Optional[str] = Query(None),
    user_id: UUID = Depends(get_current_user_id),
    use_case = Depends(get_use_case("list_facet_progress_use_case"))
):
    """List progress for all facets."""
    return await use_case.execute(user_id, mastery_level)


@router.get("/leaderboard", response_model=List[LeaderboardEntryResponse])
async def get_leaderboard(
    scope: str = Query("global", regex="^(global|topic|facet)$"),
    scope_id: Optional[UUID] = Query(None),
    timeframe: str = Query("all", regex="^(today|week|month|all)$"),
    limit: int = Query(10, ge=1, le=100),
    use_case: GetLeaderboardUseCase = Depends(get_use_case("get_leaderboard_use_case"))
):
    """Get leaderboard."""
    return await use_case.execute(scope, scope_id, timeframe, limit)


@router.get("/streak")
async def get_streak_info(
    user_id: UUID = Depends(get_current_user_id),
    use_case = Depends(get_use_case("get_streak_info_use_case"))
):
    """Get streak information."""
    return await use_case.execute(user_id)


@router.post("/streak/update")
async def update_streak(
    user_id: UUID = Depends(get_current_user_id),
    use_case = Depends(get_use_case("update_streak_use_case"))
):
    """Update daily streak."""
    return await use_case.execute(user_id)