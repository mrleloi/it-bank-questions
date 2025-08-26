"""Learning-related models."""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from .base import BaseModel
from .user_models import UserModel
from .question_models import QuestionModel
from .content_models import FacetModel


class LearningSessionModel(BaseModel):
    """Learning session model."""

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
    ]

    user = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        related_name='learning_sessions'
    )
    facet = models.ForeignKey(
        FacetModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sessions'
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        db_index=True
    )

    # Timing
    started_at = models.DateTimeField(auto_now_add=True, db_index=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    last_activity_at = models.DateTimeField(auto_now=True)

    # Configuration
    question_limit = models.IntegerField(null=True, blank=True)
    time_limit_minutes = models.IntegerField(null=True, blank=True)
    question_types = models.JSONField(
        models.CharField(max_length=20),
        default=list,
        blank=True
    )
    difficulty_min = models.IntegerField(default=1)
    difficulty_max = models.IntegerField(default=5)

    # Queue management (JSON)
    question_queue = models.JSONField(default=list)  # List of question IDs
    answered_questions = models.JSONField(default=list)
    current_question_id = models.UUIDField(null=True, blank=True)
    current_question_started_at = models.DateTimeField(null=True, blank=True)

    # Metrics
    total_questions = models.IntegerField(default=0)
    answered_questions_count = models.IntegerField(default=0)
    correct_answers = models.IntegerField(default=0)
    total_time_seconds = models.IntegerField(default=0)
    active_time_seconds = models.IntegerField(default=0)

    # Additional metrics (JSON)
    metrics = models.JSONField(default=dict)

    class Meta:
        db_table = 'learning_sessions'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'started_at']),
            models.Index(fields=['facet', 'status']),
        ]

    def __str__(self):
        return f"Session {self.id} - {self.user.username}"

    @property
    def accuracy_rate(self):
        """Calculate accuracy rate."""
        if self.answered_questions_count == 0:
            return 0.0
        return (self.correct_answers / self.answered_questions_count) * 100

    @property
    def average_time_per_question(self):
        """Calculate average time per question."""
        if self.answered_questions_count == 0:
            return 0.0
        return self.active_time_seconds / self.answered_questions_count


class UserResponseModel(BaseModel):
    """User response to a question."""

    user = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        related_name='responses'
    )
    question = models.ForeignKey(
        QuestionModel,
        on_delete=models.CASCADE,
        related_name='user_responses'
    )
    session = models.ForeignKey(
        LearningSessionModel,
        on_delete=models.CASCADE,
        related_name='responses'
    )

    # Response
    response_text = models.TextField(blank=True)  # For theory/scenario
    selected_option = models.CharField(max_length=10, blank=True)  # For MCQ
    is_correct = models.BooleanField(null=True)  # None for non-MCQ in Phase 1

    # User feedback
    difficulty_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(4)],
        null=True,
        blank=True
    )
    confidence_level = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )

    # Timing
    time_spent_seconds = models.IntegerField(default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)

    # Hints used
    hints_used = models.IntegerField(default=0)
    hint_levels = models.JSONField(
        models.IntegerField(),
        default=list,
        blank=True
    )

    # AI evaluation (Phase 2)
    ai_score = models.FloatField(null=True, blank=True)
    ai_feedback = models.TextField(blank=True)

    # Additional metadata (JSON)
    metadata = models.JSONField(default=dict)

    class Meta:
        db_table = 'user_responses'
        indexes = [
            models.Index(fields=['user', 'question']),
            models.Index(fields=['session', 'created_at']),
            models.Index(fields=['user', 'is_correct']),
        ]
        unique_together = [['user', 'question', 'session']]

    def __str__(self):
        return f"{self.user.username} - {self.question.external_id}"


class SpacedRepetitionCardModel(BaseModel):
    """Spaced repetition card model."""

    STATE_CHOICES = [
        ('new', 'New'),
        ('learning', 'Learning'),
        ('review', 'Review'),
        ('relearning', 'Relearning'),
        ('suspended', 'Suspended'),
        ('buried', 'Buried'),
    ]

    user = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        related_name='spaced_cards'
    )
    question = models.ForeignKey(
        QuestionModel,
        on_delete=models.CASCADE,
        related_name='spaced_cards'
    )

    # Card state
    state = models.CharField(
        max_length=20,
        choices=STATE_CHOICES,
        default='new',
        db_index=True
    )

    # Spaced repetition parameters
    ease_factor = models.FloatField(default=2.5)
    interval_days = models.IntegerField(default=0)
    due_date = models.DateTimeField(db_index=True)

    # Learning phase
    learning_step = models.IntegerField(default=0)

    # Review history
    last_reviewed_at = models.DateTimeField(null=True, blank=True)
    total_reviews = models.IntegerField(default=0)
    total_correct = models.IntegerField(default=0)
    total_time_seconds = models.IntegerField(default=0)

    # Lapse tracking
    lapses = models.IntegerField(default=0)

    # Statistics
    last_ease_factor = models.FloatField(default=2.5)
    last_interval_days = models.IntegerField(default=0)

    # Review configuration (JSON)
    review_config = models.JSONField(default=dict)

    class Meta:
        db_table = 'spaced_repetition_cards'
        indexes = [
            models.Index(fields=['user', 'due_date']),
            models.Index(fields=['user', 'state']),
            models.Index(fields=['user', 'question']),
        ]
        unique_together = [['user', 'question']]

    def __str__(self):
        return f"{self.user.username} - {self.question.external_id} ({self.state})"

    @property
    def is_leech(self):
        """Check if card is a leech (difficult card)."""
        threshold = self.review_config.get('leech_threshold', 8)
        return self.lapses >= threshold

    @property
    def accuracy_rate(self):
        """Calculate accuracy rate."""
        if self.total_reviews == 0:
            return 0.0
        return (self.total_correct / self.total_reviews) * 100
