"""Progress mapper."""

from typing import List
from uuid import UUID

from domain.entities import UserProgress, FacetProgress
from application.dto.response import UserProgressResponse, FacetProgressResponse


class ProgressMapper:
    """Mapper for Progress entities and DTOs."""

    @staticmethod
    def facet_to_response_dto(
            progress: FacetProgress,
            facet_name: str = None
    ) -> FacetProgressResponse:
        """Convert FacetProgress entity to response DTO."""
        return FacetProgressResponse(
            facet_id=progress.facet_id,
            facet_name=facet_name or "Unknown",
            total_questions=progress.total_questions,
            seen_questions=progress.seen_questions,
            mastered_questions=progress.mastered_questions,
            completion_percentage=progress.completion_percentage,
            mastery_score=progress.mastery_score,
            mastery_level=progress.mastery_level.value,
            accuracy_rate=progress.accuracy_rate,
            current_streak_days=progress.current_streak_days,
            last_activity_at=progress.last_activity_at
        )

    @staticmethod
    def user_to_response_dto(
            progress: UserProgress,
            facet_responses: List[FacetProgressResponse] = None
    ) -> UserProgressResponse:
        """Convert UserProgress entity to response DTO."""
        return UserProgressResponse(
            user_id=progress.user_id,
            overall_mastery_score=progress.overall_mastery_score,
            total_study_time_seconds=progress.total_study_time_seconds,
            total_questions_answered=progress.total_questions_answered,
            total_correct_answers=progress.total_correct_answers,
            achievement_points=progress.achievement_points,
            facet_progresses=facet_responses or [],
            preferred_study_time=progress.preferred_study_time,
            average_session_length_minutes=progress.average_session_length_minutes,
            most_productive_day=progress.most_productive_day
        )