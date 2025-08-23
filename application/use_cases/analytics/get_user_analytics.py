"""Get user analytics use case."""

from typing import Dict, Any
from uuid import UUID

from domain.services import AnalyticsService
from application.dto.response import (
    StudyPatternResponse,
    PerformanceTrendResponse,
    LearningVelocityResponse
)


class GetUserAnalyticsUseCase:
    """Use case for getting user analytics."""

    def __init__(self, analytics_service: AnalyticsService):
        self.analytics = analytics_service

    async def execute(
            self,
            user_id: UUID,
            period_days: int = 30
    ) -> Dict[str, Any]:
        """Get comprehensive user analytics."""
        # Get analytics from domain service
        analytics_data = await self.analytics.get_user_analytics(
            user_id, period_days
        )

        # Map to response DTOs
        study_patterns = StudyPatternResponse(
            peak_hour=analytics_data['study_patterns']['peak_hour'],
            peak_day=analytics_data['study_patterns']['peak_day'],
            hourly_distribution=analytics_data['study_patterns']['hourly_distribution'],
            daily_distribution=analytics_data['study_patterns']['daily_distribution'],
            consistency_score=analytics_data['study_patterns']['consistency_score']
        )

        performance_trends = PerformanceTrendResponse(
            trend=analytics_data['performance_trends']['trend'],
            improvement_rate=analytics_data['performance_trends']['improvement_rate'],
            recent_accuracy=analytics_data['performance_trends']['recent_accuracy'],
            average_accuracy=analytics_data['performance_trends']['average_accuracy']
        )

        learning_velocity = LearningVelocityResponse(
            questions_per_day=analytics_data['learning_velocity']['questions_per_day'],
            mastery_growth_rate=analytics_data['learning_velocity']['mastery_growth_rate'],
            estimated_completion_days=analytics_data['learning_velocity'].get('estimated_total_completion_days')
        )

        return {
            'period_days': period_days,
            'study_patterns': study_patterns.to_dict(),
            'performance_trends': performance_trends.to_dict(),
            'learning_velocity': learning_velocity.to_dict(),
            'question_statistics': analytics_data['question_statistics'],
            'session_metrics': analytics_data['session_metrics'],
            'strengths_weaknesses': analytics_data['strengths_weaknesses']
        }