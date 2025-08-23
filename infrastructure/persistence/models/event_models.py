"""Event sourcing models."""

from django.db import models
from .base import BaseModel
from .user_models import UserModel
from .question_models import QuestionModel
from .learning_models import LearningSessionModel
from .content_models import FacetModel


class LearningEventModel(BaseModel):
    """Learning event for analytics and event sourcing."""

    EVENT_TYPE_CHOICES = [
        # Session events
        ('session_started', 'Session Started'),
        ('session_completed', 'Session Completed'),
        ('session_abandoned', 'Session Abandoned'),

        # Question events
        ('question_viewed', 'Question Viewed'),
        ('question_answered', 'Question Answered'),
        ('question_skipped', 'Question Skipped'),
        ('hint_requested', 'Hint Requested'),

        # Review events
        ('card_reviewed', 'Card Reviewed'),
        ('card_suspended', 'Card Suspended'),
        ('card_buried', 'Card Buried'),

        # Progress events
        ('facet_completed', 'Facet Completed'),
        ('facet_mastered', 'Facet Mastered'),
        ('achievement_unlocked', 'Achievement Unlocked'),
        ('streak_updated', 'Streak Updated'),

        # User events
        ('user_registered', 'User Registered'),
        ('user_login', 'User Login'),
        ('user_logout', 'User Logout'),
        ('settings_updated', 'Settings Updated'),

        # Phase 2: AI events
        ('ai_hint_generated', 'AI Hint Generated'),
        ('ai_feedback_provided', 'AI Feedback Provided'),
        ('ai_chat_message', 'AI Chat Message'),
    ]

    user = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        related_name='learning_events'
    )
    event_type = models.CharField(
        max_length=50,
        choices=EVENT_TYPE_CHOICES,
        db_index=True
    )

    # Optional relations
    session = models.ForeignKey(
        LearningSessionModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='events'
    )
    question = models.ForeignKey(
        QuestionModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='events'
    )
    facet = models.ForeignKey(
        FacetModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='events'
    )

    # Event data (JSON)
    event_data = models.JSONField(default=dict)

    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    device_type = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = 'learning_events'
        indexes = [
            models.Index(fields=['user', 'event_type', 'created_at']),
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['session', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.event_type} at {self.created_at}"