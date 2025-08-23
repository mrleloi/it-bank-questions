"""Analytics-related Celery tasks."""

from datetime import datetime, timedelta
from celery import shared_task
from django.db.models import Count, Avg, Sum, F

from infrastructure.persistence.models import (
    UserModel,
    LearningEventModel,
    FacetProgressModel,
    UserProgressModel
)


@shared_task
def calculate_daily_statistics():
    """Calculate daily statistics for all users."""
    yesterday = datetime.now() - timedelta(days=1)

    users = UserModel.objects.filter(
        status='active',
        learning_events__created_at__gte=yesterday
    ).distinct()

    for user in users:
        # Calculate daily stats
        events = LearningEventModel.objects.filter(
            user=user,
            created_at__gte=yesterday
        )

        questions_answered = events.filter(
            event_type='question_answered'
        ).count()

        sessions_completed = events.filter(
            event_type='session_completed'
        ).count()

        # Update user progress
        progress, created = UserProgressModel.objects.get_or_create(user=user)
        progress.total_questions_answered += questions_answered

        # Calculate average session length
        if sessions_completed > 0:
            avg_session_time = events.filter(
                event_type='session_completed'
            ).aggregate(
                avg_time=Avg('event_data__total_time_seconds')
            )['avg_time'] or 0

            progress.average_session_length_minutes = avg_session_time / 60

        progress.save()

    return {
        'users_processed': users.count()
    }


@shared_task
def generate_learning_insights(user_id: str):
    """Generate learning insights for a user."""
    user = UserModel.objects.get(id=user_id)

    # Get last 30 days of events
    start_date = datetime.now() - timedelta(days=30)
    events = LearningEventModel.objects.filter(
        user=user,
        created_at__gte=start_date
    )

    # Analyze study patterns
    study_hours = {}
    study_days = {}

    for event in events:
        hour = event.created_at.hour
        day = event.created_at.strftime('%A')

        study_hours[hour] = study_hours.get(hour, 0) + 1
        study_days[day] = study_days.get(day, 0) + 1

    # Find peak times
    peak_hour = max(study_hours.items(), key=lambda x: x[1])[0] if study_hours else None
    peak_day = max(study_days.items(), key=lambda x: x[1])[0] if study_days else None

    # Update user progress
    progress, created = UserProgressModel.objects.get_or_create(user=user)

    if peak_hour:
        if peak_hour < 6:
            progress.preferred_study_time = 'early_morning'
        elif peak_hour < 12:
            progress.preferred_study_time = 'morning'
        elif peak_hour < 17:
            progress.preferred_study_time = 'afternoon'
        elif peak_hour < 21:
            progress.preferred_study_time = 'evening'
        else:
            progress.preferred_study_time = 'night'

    progress.most_productive_day = peak_day
    progress.save()

    return {
        'user_id': str(user_id),
        'peak_hour': peak_hour,
        'peak_day': peak_day,
        'events_analyzed': events.count()
    }


@shared_task
def calculate_facet_statistics():
    """Calculate statistics for all facets."""
    from infrastructure.persistence.models import FacetModel

    facets = FacetModel.objects.all()

    for facet in facets:
        # Count questions
        facet.total_questions = facet.questions.filter(is_active=True).count()

        # Count learners
        facet.total_learners = FacetProgressModel.objects.filter(
            facet=facet,
            seen_questions__gt=0
        ).count()

        # Calculate average mastery
        avg_mastery = FacetProgressModel.objects.filter(
            facet=facet
        ).aggregate(
            avg=Avg('mastery_score')
        )['avg'] or 0

        facet.average_mastery = avg_mastery
        facet.save()

    return {
        'facets_updated': facets.count()
    }
