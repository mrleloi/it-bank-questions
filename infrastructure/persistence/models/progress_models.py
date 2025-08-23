"""Progress tracking models."""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from .base import BaseModel
from .user_models import UserModel
from .content_models import FacetModel


class FacetProgressModel(BaseModel):
    """Progress for a specific facet."""

    user = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        related_name='facet_progress'
    )
    facet = models.ForeignKey(
        FacetModel,
        on_delete=models.CASCADE,
        related_name='user_progress'
    )

    # Question tracking
    total_questions = models.IntegerField(default=0)
    seen_questions = models.IntegerField(default=0)
    mastered_questions = models.IntegerField(default=0)

    # Performance metrics
    mastery_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    accuracy_rate = models.FloatField(default=0.0)
    average_response_time = models.FloatField(default=0.0)
    difficulty_comfort = models.FloatField(
        default=3.0,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    # Activity tracking
    last_activity_at = models.DateTimeField(null=True, blank=True)
    total_time_spent_seconds = models.IntegerField(default=0)

    # Streak tracking
    current_streak_days = models.IntegerField(default=0)
    longest_streak_days = models.IntegerField(default=0)
    last_streak_date = models.DateField(null=True, blank=True)

    # Additional metrics (JSON)
    metrics = models.JSONField(default=dict)

    class Meta:
        db_table = 'facet_progress'
        indexes = [
            models.Index(fields=['user', 'mastery_score']),
            models.Index(fields=['user', 'last_activity_at']),
        ]
        unique_together = [['user', 'facet']]

    def __str__(self):
        return f"{self.user.username} - {self.facet.code} ({self.mastery_score}%)"

    @property
    def completion_percentage(self):
        """Calculate completion percentage."""
        if self.total_questions == 0:
            return 0.0
        return (self.seen_questions / self.total_questions) * 100

    @property
    def mastery_percentage(self):
        """Calculate mastery percentage."""
        if self.total_questions == 0:
            return 0.0
        return (self.mastered_questions / self.total_questions) * 100

    @property
    def mastery_level(self):
        """Get mastery level based on score."""
        if self.mastery_score < 20:
                return 'novice'
        elif self.mastery_score < 40:
            return 'beginner'
        elif self.mastery_score < 60:
            return 'intermediate'
        elif self.mastery_score < 80:
            return 'advanced'
        else:
            return 'expert'


class UserProgressModel(BaseModel):
    """Overall user progress."""

    user = models.OneToOneField(
        UserModel,
        on_delete=models.CASCADE,
        related_name='overall_progress'
    )

    # Global metrics
    total_study_time_seconds = models.IntegerField(default=0)
    total_questions_answered = models.IntegerField(default=0)
    total_correct_answers = models.IntegerField(default=0)
    overall_mastery_score = models.FloatField(default=0.0)

    # Achievements
    achievements_unlocked = models.JSONField(default=list)  # List of achievement names
    achievement_points = models.IntegerField(default=0)

    # Learning patterns
    preferred_study_time = models.CharField(max_length=20, blank=True)
    average_session_length_minutes = models.FloatField(default=0.0)
    most_productive_day = models.CharField(max_length=20, blank=True)

    # Additional analytics (JSON)
    analytics = models.JSONField(default=dict)

    class Meta:
        db_table = 'user_progress'

    def __str__(self):
        return f"{self.user.username} - Overall Progress"
