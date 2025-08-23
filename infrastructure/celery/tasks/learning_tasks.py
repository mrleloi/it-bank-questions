"""Learning-related Celery tasks."""

from datetime import datetime, timedelta
from celery import shared_task
from django.db import transaction
from django.db.models import F, Q

from infrastructure.persistence.models import (
    UserModel,
    SpacedRepetitionCardModel,
    LearningSessionModel,
    QuestionModel
)


@shared_task
def generate_daily_review_cards(user_id: str = None):
    """Generate daily review cards for users."""
    query = UserModel.objects.filter(status='active', is_deleted=False)

    if user_id:
        query = query.filter(id=user_id)

    users = query.all()
    total_cards = 0

    for user in users:
        # Get all questions user hasn't seen
        seen_question_ids = SpacedRepetitionCardModel.objects.filter(
            user=user
        ).values_list('question_id', flat=True)

        new_questions = QuestionModel.objects.filter(
            is_active=True
        ).exclude(
            id__in=seen_question_ids
        )[:user.preferences.daily_goal]

        # Create cards for new questions
        cards = []
        for question in new_questions:
            card = SpacedRepetitionCardModel(
                user=user,
                question=question,
                due_date=datetime.now(),
                state='new'
            )
            cards.append(card)

        if cards:
            SpacedRepetitionCardModel.objects.bulk_create(cards)
            total_cards += len(cards)

    return {
        'users_processed': len(users),
        'cards_created': total_cards
    }


@shared_task
def process_overdue_cards():
    """Process overdue spaced repetition cards."""
    overdue_threshold = datetime.now() - timedelta(days=7)

    overdue_cards = SpacedRepetitionCardModel.objects.filter(
        due_date__lt=overdue_threshold,
        state__in=['review', 'learning']
    )

    count = 0
    for card in overdue_cards:
        # Reset interval for very overdue cards
        card.interval_days = 1
        card.ease_factor = max(1.3, card.ease_factor - 0.2)
        card.due_date = datetime.now()
        card.save()
        count += 1

    return {
        'cards_processed': count
    }


@shared_task
def cleanup_expired_sessions():
    """Clean up expired learning sessions."""
    expiry_time = datetime.now() - timedelta(minutes=30)

    expired_sessions = LearningSessionModel.objects.filter(
        status='active',
        last_activity_at__lt=expiry_time
    )

    count = 0
    for session in expired_sessions:
        session.status = 'abandoned'
        session.ended_at = session.last_activity_at
        session.save()
        count += 1

    return {
        'sessions_expired': count
    }


@shared_task
def calculate_question_statistics():
    """Calculate and update question statistics."""
    questions = QuestionModel.objects.filter(
        times_answered__gt=0
    )

    for question in questions:
        responses = question.user_responses.all()

        if responses:
            # Calculate success rate
            correct_count = responses.filter(is_correct=True).count()
            question.success_rate = (correct_count / responses.count()) * 100

            # Calculate average time
            total_time = sum(r.time_spent_seconds for r in responses)
            question.average_time_seconds = total_time / responses.count()

            question.save()

    return {
        'questions_updated': questions.count()
    }
