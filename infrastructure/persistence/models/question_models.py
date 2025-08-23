"""Question-related models."""

from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator
from .base import BaseModel
from .content_models import FacetModel


class QuestionModel(BaseModel):
    """Question model."""

    TYPE_CHOICES = [
        ('mcq', 'Multiple Choice'),
        ('theory', 'Theory'),
        ('scenario', 'Scenario'),
    ]

    SOURCE_CHOICES = [
        ('hard_resource', 'Hard Resource'),
        ('user_generated', 'User Generated'),
        ('ai_generated', 'AI Generated'),
        ('admin_imported', 'Admin Imported'),
    ]

    # Identification
    external_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True
    )
    facet = models.ForeignKey(
        FacetModel,
        on_delete=models.CASCADE,
        related_name='questions'
    )

    # Content
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        db_index=True
    )
    question = models.TextField()
    difficulty_level = models.IntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        db_index=True
    )

    # Metadata
    source = models.CharField(
        max_length=50,
        choices=SOURCE_CHOICES,
        default='hard_resource',
        db_index=True
    )
    tags = ArrayField(
        models.CharField(max_length=50),
        default=list,
        blank=True,
        db_index=True
    )
    estimated_time_seconds = models.IntegerField(null=True, blank=True)

    # For theory/scenario questions
    sample_answer = models.TextField(blank=True)
    evaluation_criteria = models.TextField(blank=True)

    # Hints (JSON array)
    hints = models.JSONField(default=list)

    # References and learning materials
    references = ArrayField(
        models.URLField(),
        default=list,
        blank=True
    )
    learning_objectives = ArrayField(
        models.CharField(max_length=255),
        default=list,
        blank=True
    )
    prerequisites = ArrayField(
        models.CharField(max_length=255),
        default=list,
        blank=True
    )

    # Statistics
    times_answered = models.IntegerField(default=0)
    times_correct = models.IntegerField(default=0)
    average_time_seconds = models.FloatField(null=True, blank=True)
    success_rate = models.FloatField(null=True, blank=True)

    # AI fields for Phase 2
    ai_generated = models.BooleanField(default=False)
    ai_difficulty_assessment = models.FloatField(null=True, blank=True)
    community_rating = models.FloatField(null=True, blank=True)

    # Status
    is_active = models.BooleanField(default=True, db_index=True)
    needs_review = models.BooleanField(default=False)

    # Additional metadata (JSON)
    metadata = models.JSONField(default=dict)

    class Meta:
        db_table = 'questions'
        indexes = [
            models.Index(fields=['facet', 'type']),
            models.Index(fields=['facet', 'difficulty_level']),
            models.Index(fields=['source', 'is_active']),
            models.Index(fields=['external_id']),
        ]

    def __str__(self):
        return f"{self.external_id} - {self.question[:50]}"

    def update_statistics(self, is_correct, time_seconds):
        """Update question statistics after answer."""
        self.times_answered += 1
        if is_correct:
            self.times_correct += 1

        # Update average time
        if self.average_time_seconds is None:
            self.average_time_seconds = time_seconds
        else:
            self.average_time_seconds = (
                    (self.average_time_seconds * (self.times_answered - 1) + time_seconds)
                    / self.times_answered
            )

        # Update success rate
        self.success_rate = (self.times_correct / self.times_answered) * 100

        self.save()


class MCQOptionModel(BaseModel):
    """MCQ option model."""

    question = models.ForeignKey(
        QuestionModel,
        on_delete=models.CASCADE,
        related_name='mcq_options'
    )
    option_key = models.CharField(max_length=10)  # A, B, C, D, etc.
    option_text = models.TextField()
    is_correct = models.BooleanField(default=False)
    explanation = models.TextField(blank=True)

    class Meta:
        db_table = 'mcq_options'
        ordering = ['option_key']
        unique_together = [['question', 'option_key']]

    def __str__(self):
        return f"{self.question.external_id} - {self.option_key}"
