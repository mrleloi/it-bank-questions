"""Analytics domain service."""

from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from collections import defaultdict

from ..entities import LearningEvent, LearningSession
from ..entities.learning_event import EventType
from ..repositories import (
    EventRepository,
    SessionRepository,
    ProgressRepository,
    QuestionRepository
)


class AnalyticsService:
    """Service for learning analytics."""

    def __init__(
            self,
            event_repo: EventRepository,
            session_repo: SessionRepository,
            progress_repo: ProgressRepository,
            question_repo: QuestionRepository
    ):
        self.event_repo = event_repo
        self.session_repo = session_repo
        self.progress_repo = progress_repo
        self.question_repo = question_repo

    async def get_user_analytics(
            self,
            user_id: UUID,
            period_days: int = 30
    ) -> Dict[str, Any]:
        """Get comprehensive analytics for a user."""
        start_date = datetime.now() - timedelta(days=period_days)

        # Get events for analysis
        events = await self.event_repo.get_user_events(
            user_id,
            start_date=start_date
        )

        # Get sessions
        sessions = await self.session_repo.get_sessions_in_period(
            user_id,
            start_date,
            datetime.now()
        )

        # Calculate metrics
        analytics = {
            'period_days': period_days,
            'study_patterns': await self._analyze_study_patterns(events),
            'performance_trends': await self._analyze_performance_trends(
                user_id, sessions
            ),
            'question_statistics': await self._analyze_question_statistics(
                events
            ),
            'session_metrics': self._analyze_session_metrics(sessions),
            'learning_velocity': await self._calculate_learning_velocity(
                user_id, period_days
            ),
            'strengths_weaknesses': await self._identify_strengths_weaknesses(
                user_id
            )
        }

        return analytics

    async def get_global_analytics(
            self,
            period_days: int = 30
    ) -> Dict[str, Any]:
        """Get platform-wide analytics."""
        start_date = datetime.now() - timedelta(days=period_days)

        # Get all events for period
        events = await self.event_repo.get_events_by_type(
            None,  # All types
            start_date=start_date
        )

        analytics = {
            'period_days': period_days,
            'active_users': len(set(e.user_id for e in events)),
            'total_questions_answered': sum(
                1 for e in events
                if e.event_type == EventType.QUESTION_ANSWERED
            ),
            'total_sessions': sum(
                1 for e in events
                if e.event_type == EventType.SESSION_STARTED
            ),
            'popular_topics': await self._get_popular_topics(events),
            'peak_hours': self._analyze_peak_hours(events),
            'achievement_distribution': await self._get_achievement_distribution(
                events
            )
        }

        return analytics

    async def predict_completion(
            self,
            user_id: UUID,
            facet_id: UUID
    ) -> Dict[str, Any]:
        """Predict when user will complete a facet."""
        progress = await self.progress_repo.get_facet_progress(
            user_id, facet_id
        )

        if not progress:
            return {
                'status': 'not_started',
                'estimated_days': None
            }

        # Get recent learning velocity
        recent_events = await self.event_repo.get_user_events(
            user_id,
            start_date=datetime.now() - timedelta(days=7)
        )

        questions_per_day = len([
            e for e in recent_events
            if e.event_type == EventType.QUESTION_ANSWERED
        ]) / 7.0

        if questions_per_day == 0:
            return {
                'status': 'inactive',
                'estimated_days': None
            }

        remaining_questions = progress.total_questions - progress.seen_questions
        estimated_days = remaining_questions / questions_per_day

        return {
            'status': 'in_progress',
            'estimated_days': int(estimated_days),
            'completion_date': (
                    datetime.now() + timedelta(days=estimated_days)
            ).date().isoformat(),
            'confidence': self._calculate_prediction_confidence(progress),
            'remaining_questions': remaining_questions,
            'daily_average': round(questions_per_day, 1)
        }

    async def _analyze_study_patterns(
            self,
            events: List[LearningEvent]
    ) -> Dict[str, Any]:
        """Analyze user's study patterns."""
        study_hours = defaultdict(int)
        study_days = defaultdict(int)

        for event in events:
            if event.event_type in [
                EventType.SESSION_STARTED,
                EventType.QUESTION_ANSWERED
            ]:
                hour = event.created_at.hour
                day = event.created_at.strftime('%A')

                study_hours[hour] += 1
                study_days[day] += 1

        # Find peak times
        peak_hour = max(study_hours.items(), key=lambda x: x[1])[0] if study_hours else None
        peak_day = max(study_days.items(), key=lambda x: x[1])[0] if study_days else None

        return {
            'peak_hour': peak_hour,
            'peak_day': peak_day,
            'hourly_distribution': dict(study_hours),
            'daily_distribution': dict(study_days),
            'consistency_score': self._calculate_consistency_score(events)
        }

    async def _analyze_performance_trends(
            self,
            user_id: UUID,
            sessions: List[LearningSession]
    ) -> Dict[str, Any]:
        """Analyze performance trends over time."""
        if not sessions:
            return {
                'trend': 'no_data',
                'improvement_rate': 0
            }

        # Sort sessions by date
        sessions.sort(key=lambda s: s.started_at)

        # Calculate accuracy trend
        accuracies = [s.metrics.accuracy_rate for s in sessions]

        # Simple linear regression for trend
        if len(accuracies) > 1:
            # Calculate slope
            n = len(accuracies)
            x_mean = (n - 1) / 2
            y_mean = sum(accuracies) / n

            numerator = sum((i - x_mean) * (acc - y_mean)
                            for i, acc in enumerate(accuracies))
            denominator = sum((i - x_mean) ** 2 for i in range(n))

            slope = numerator / denominator if denominator != 0 else 0

            trend = 'improving' if slope > 0.5 else 'declining' if slope < -0.5 else 'stable'
        else:
            slope = 0
            trend = 'insufficient_data'

        return {
            'trend': trend,
            'improvement_rate': slope,
            'recent_accuracy': accuracies[-1] if accuracies else 0,
            'average_accuracy': sum(accuracies) / len(accuracies) if accuracies else 0
        }

    async def _analyze_question_statistics(
            self,
            events: List[LearningEvent]
    ) -> Dict[str, Any]:
        """Analyze question-related statistics."""
        question_events = [
            e for e in events
            if e.event_type == EventType.QUESTION_ANSWERED
        ]

        if not question_events:
            return {
                'total_answered': 0,
                'accuracy_rate': 0,
                'average_time': 0
            }

        correct_count = sum(
            1 for e in question_events
            if e.event_data.get('is_correct', False)
        )

        total_time = sum(
            e.event_data.get('time_seconds', 0)
            for e in question_events
        )

        return {
            'total_answered': len(question_events),
            'correct_answers': correct_count,
            'accuracy_rate': (correct_count / len(question_events)) * 100,
            'average_time': total_time / len(question_events) if question_events else 0,
            'difficulty_distribution': self._get_difficulty_distribution(
                question_events
            )
        }

    def _analyze_session_metrics(
            self,
            sessions: List[LearningSession]
    ) -> Dict[str, Any]:
        """Analyze session metrics."""
        if not sessions:
            return {
                'total_sessions': 0,
                'average_duration': 0,
                'completion_rate': 0
            }

        completed = [s for s in sessions if s.status.value == 'completed']
        total_time = sum(s.metrics.total_time_seconds for s in sessions)

        return {
            'total_sessions': len(sessions),
            'completed_sessions': len(completed),
            'completion_rate': (len(completed) / len(sessions)) * 100,
            'average_duration': total_time / len(sessions) / 60,  # in minutes
            'average_questions_per_session': sum(
                s.metrics.answered_questions for s in sessions
            ) / len(sessions)
        }

    async def _calculate_learning_velocity(
            self,
            user_id: UUID,
            period_days: int
    ) -> Dict[str, Any]:
        """Calculate learning velocity metrics."""
        progress = await self.progress_repo.get_user_progress(user_id)

        # Calculate questions per day
        questions_per_day = progress.total_questions_answered / period_days

        # Calculate mastery growth rate
        mastery_growth = sum(
            p.mastery_score for p in progress.facet_progresses.values()
        ) / len(progress.facet_progresses) if progress.facet_progresses else 0

        return {
            'questions_per_day': round(questions_per_day, 1),
            'mastery_growth_rate': round(mastery_growth / period_days, 2),
            'estimated_total_completion_days': self._estimate_total_completion(
                progress, questions_per_day
            )
        }

    async def _identify_strengths_weaknesses(
            self,
            user_id: UUID
    ) -> Dict[str, Any]:
        """Identify user's strengths and weaknesses."""
        progress = await self.progress_repo.get_user_progress(user_id)

        if not progress.facet_progresses:
            return {
                'strengths': [],
                'weaknesses': [],
                'recommendations': []
            }

        # Sort facets by performance
        facet_performance = []
        for facet_id, facet_progress in progress.facet_progresses.items():
            facet_performance.append({
                'facet_id': str(facet_id),
                'accuracy': facet_progress.accuracy_rate,
                'mastery': facet_progress.mastery_score,
                'difficulty_comfort': facet_progress.difficulty_comfort
            })

        # Sort by mastery score
        facet_performance.sort(key=lambda x: x['mastery'], reverse=True)

        strengths = facet_performance[:3] if len(facet_performance) >= 3 else facet_performance
        weaknesses = facet_performance[-3:] if len(facet_performance) >= 3 else []

        return {
            'strengths': strengths,
            'weaknesses': weaknesses,
            'recommendations': await self._generate_recommendations(weaknesses)
        }

    def _calculate_consistency_score(
            self,
            events: List[LearningEvent]
    ) -> float:
        """Calculate study consistency score (0-100)."""
        if not events:
            return 0.0

        # Group events by date
        study_dates = set()
        for event in events:
            if event.event_type in [
                EventType.SESSION_STARTED,
                EventType.QUESTION_ANSWERED
            ]:
                study_dates.add(event.created_at.date())

        if not study_dates:
            return 0.0

        # Calculate gaps between study dates
        sorted_dates = sorted(study_dates)
        if len(sorted_dates) < 2:
            return 100.0

        gaps = []
        for i in range(1, len(sorted_dates)):
            gap = (sorted_dates[i] - sorted_dates[i - 1]).days
            gaps.append(gap)

        # Score based on average gap (1 day = perfect)
        avg_gap = sum(gaps) / len(gaps)
        if avg_gap <= 1:
            score = 100.0
        elif avg_gap <= 2:
            score = 80.0
        elif avg_gap <= 3:
            score = 60.0
        elif avg_gap <= 5:
            score = 40.0
        else:
            score = 20.0

        return score

    def _calculate_prediction_confidence(
            self,
            progress: Any
    ) -> float:
        """Calculate confidence in completion prediction."""
        # Based on consistency and data availability
        if progress.current_streak_days > 7:
            confidence = 0.9
        elif progress.current_streak_days > 3:
            confidence = 0.7
        else:
            confidence = 0.5

        # Adjust based on completion percentage
        if progress.completion_percentage > 50:
            confidence += 0.1

        return min(1.0, confidence)

    def _get_difficulty_distribution(
            self,
            question_events: List[LearningEvent]
    ) -> Dict[int, int]:
        """Get distribution of question difficulties."""
        distribution = defaultdict(int)

        for event in question_events:
            difficulty = event.event_data.get('difficulty_level', 3)
            distribution[difficulty] += 1

        return dict(distribution)

    def _estimate_total_completion(
            self,
            progress: Any,
            questions_per_day: float
    ) -> Optional[int]:
        """Estimate days to complete all content."""
        if questions_per_day == 0:
            return None

        # This would need to query total questions across all facets
        # Simplified estimation
        return 365  # Placeholder

    async def _generate_recommendations(
            self,
            weaknesses: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations based on weaknesses."""
        recommendations = []

        for weakness in weaknesses:
            if weakness['accuracy'] < 50:
                recommendations.append(
                    f"Review facet {weakness['facet_id']} - focus on understanding concepts"
                )
            if weakness['difficulty_comfort'] < 2:
                recommendations.append(
                    f"Practice easier questions in facet {weakness['facet_id']} to build confidence"
                )

        return recommendations[:3]  # Top 3 recommendations

    async def _get_popular_topics(
            self,
            events: List[LearningEvent]
    ) -> List[Dict[str, Any]]:
        """Get most popular topics based on activity."""
        # This would aggregate by topic
        # Simplified implementation
        return []

    def _analyze_peak_hours(
            self,
            events: List[LearningEvent]
    ) -> Dict[int, int]:
        """Analyze peak activity hours."""
        hours = defaultdict(int)

        for event in events:
            if event.event_type in [
                EventType.SESSION_STARTED,
                EventType.QUESTION_ANSWERED
            ]:
                hours[event.created_at.hour] += 1

        return dict(hours)

    async def _get_achievement_distribution(
            self,
            events: List[LearningEvent]
    ) -> Dict[str, int]:
        """Get distribution of achievements unlocked."""
        achievement_counts = defaultdict(int)

        achievement_events = [
            e for e in events
            if e.event_type == EventType.ACHIEVEMENT_UNLOCKED
        ]

        for event in achievement_events:
            achievement_name = event.event_data.get('achievement_name')
            if achievement_name:
                achievement_counts[achievement_name] += 1

        return dict(achievement_counts)