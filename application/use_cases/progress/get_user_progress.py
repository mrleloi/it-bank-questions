"""Get user progress use case."""

from typing import List
from uuid import UUID

from domain.repositories import ProgressRepository, ContentRepository
from application.dto.response import UserProgressResponse, FacetProgressResponse


class GetUserProgressUseCase:
    """Use case for getting user progress."""

    def __init__(
            self,
            progress_repository: ProgressRepository,
            content_repository: ContentRepository
    ):
        self.progress_repo = progress_repository
        self.content_repo = content_repository

    async def execute(self, user_id: UUID) -> UserProgressResponse:
        """Get comprehensive user progress."""
        # Get user progress
        user_progress = await self.progress_repo.get_user_progress(user_id)

        # Build facet progress responses
        facet_responses = []
        for facet_id, facet_progress in user_progress.facet_progresses.items():
            # Get facet details
            facet = await self.content_repo.get_facet(facet_id)

            facet_response = FacetProgressResponse(
                facet_id=facet_id,
                facet_name=facet.name if facet else "Unknown",
                total_questions=facet_progress.total_questions,
                seen_questions=facet_progress.seen_questions,
                mastered_questions=facet_progress.mastered_questions,
                completion_percentage=facet_progress.completion_percentage,
                mastery_score=facet_progress.mastery_score,
                mastery_level=facet_progress.mastery_level.value,
                accuracy_rate=facet_progress.accuracy_rate,
                current_streak_days=facet_progress.current_streak_days,
                last_activity_at=facet_progress.last_activity_at
            )
            facet_responses.append(facet_response)

        # Sort by last activity
        facet_responses.sort(
            key=lambda x: x.last_activity_at if x.last_activity_at else datetime.min,
            reverse=True
        )

        return UserProgressResponse(
            user_id=user_id,
            overall_mastery_score=user_progress.overall_mastery_score,
            total_study_time_seconds=user_progress.total_study_time_seconds,
            total_questions_answered=user_progress.total_questions_answered,
            total_correct_answers=user_progress.total_correct_answers,
            achievement_points=user_progress.achievement_points,
            facet_progresses=facet_responses,
            preferred_study_time=user_progress.preferred_study_time,
            average_session_length_minutes=user_progress.average_session_length_minutes,
            most_productive_day=user_progress.most_productive_day
        )