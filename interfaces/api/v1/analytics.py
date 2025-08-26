"""Analytics endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from application.dto.response import (
    StudyPatternResponse,
    PerformanceTrendResponse,
    LearningVelocityResponse,
    CompletionPredictionResponse
)
from ..dependencies import get_current_user_id, get_use_case

router = APIRouter()


# @router.get("/user")
# async def get_user_analytics(
#     period_days: int = Query(30, ge=1, le=365),
#     user_id: UUID = Depends(get_current_user_id),
#     use_case: GetUserAnalyticsUseCase = Depends(get_use_case("get_user_analytics_use_case"))
# ):
#     """Get comprehensive user analytics."""
#     return await use_case.execute(user_id, period_days)


@router.get("/study-patterns", response_model=StudyPatternResponse)
async def get_study_patterns(
    period_days: int = Query(30, ge=1, le=365),
    user_id: UUID = Depends(get_current_user_id),
    use_case = Depends(get_use_case("get_study_patterns_use_case"))
):
    """Get study pattern analysis."""
    return await use_case.execute(user_id, period_days)


@router.get("/performance-trends", response_model=PerformanceTrendResponse)
async def get_performance_trends(
    period_days: int = Query(30, ge=1, le=365),
    user_id: UUID = Depends(get_current_user_id),
    use_case = Depends(get_use_case("get_performance_trends_use_case"))
):
    """Get performance trend analysis."""
    return await use_case.execute(user_id, period_days)


@router.get("/learning-velocity", response_model=LearningVelocityResponse)
async def get_learning_velocity(
    period_days: int = Query(30, ge=1, le=365),
    user_id: UUID = Depends(get_current_user_id),
    use_case = Depends(get_use_case("get_learning_velocity_use_case"))
):
    """Get learning velocity metrics."""
    return await use_case.execute(user_id, period_days)


# @router.get("/predictions/completion", response_model=CompletionPredictionResponse)
# async def predict_completion(
#     facet_id: UUID = Query(...),
#     user_id: UUID = Depends(get_current_user_id),
#     use_case: GetLearningPredictionUseCase = Depends(get_use_case("get_learning_prediction_use_case"))
# ):
#     """Predict completion time for a facet."""
#     return await use_case.execute(user_id, facet_id)
#
#
# @router.get("/recommendations")
# async def get_study_recommendations(
#     limit: int = Query(5, ge=1, le=20),
#     user_id: UUID = Depends(get_current_user_id),
#     use_case: GetStudyRecommendationsUseCase = Depends(get_use_case("get_study_recommendations_use_case"))
# ):
#     """Get personalized study recommendations."""
#     return await use_case.execute(user_id, limit)


@router.get("/insights")
async def get_learning_insights(
    user_id: UUID = Depends(get_current_user_id),
    use_case = Depends(get_use_case("get_learning_insights_use_case"))
):
    """Get AI-powered learning insights."""
    # Phase 2: Will integrate with AI service
    return {
        "message": "AI insights coming in Phase 2",
        "basic_insights": [
            "You learn best in the morning",
            "Focus on reviewing difficult cards",
            "Your streak is improving retention"
        ]
    }
