"""Content hierarchy models."""

from django.db import models
from django.contrib.postgres.fields import ArrayField
from .base import BaseModel


class TopicModel(BaseModel):
    """Topic model (highest level)."""

    code = models.CharField(max_length=100, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=7, blank=True)  # Hex color
    order_index = models.IntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    # Statistics
    total_questions = models.IntegerField(default=0)
    total_learners = models.IntegerField(default=0)
    average_mastery = models.FloatField(default=0.0)
    estimated_hours = models.IntegerField(default=0)

    class Meta:
        db_table = 'topics'
        ordering = ['order_index', 'name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class SubtopicModel(BaseModel):
    """Subtopic model."""

    topic = models.ForeignKey(
        TopicModel,
        on_delete=models.CASCADE,
        related_name='subtopics'
    )
    code = models.CharField(max_length=100, db_index=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    order_index = models.IntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    # Statistics
    total_questions = models.IntegerField(default=0)
    total_learners = models.IntegerField(default=0)
    average_mastery = models.FloatField(default=0.0)

    class Meta:
        db_table = 'subtopics'
        ordering = ['order_index', 'name']
        unique_together = [['topic', 'code']]

    def __str__(self):
        return f"{self.topic.code}__{self.code} - {self.name}"


class LeafModel(BaseModel):
    """Leaf model."""

    subtopic = models.ForeignKey(
        SubtopicModel,
        on_delete=models.CASCADE,
        related_name='leaves'
    )
    code = models.CharField(max_length=100, db_index=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    order_index = models.IntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    # Statistics
    total_questions = models.IntegerField(default=0)
    total_learners = models.IntegerField(default=0)
    average_mastery = models.FloatField(default=0.0)

    class Meta:
        db_table = 'leaves'
        ordering = ['order_index', 'name']
        unique_together = [['subtopic', 'code']]

    def __str__(self):
        return f"{self.subtopic.topic.code}__{self.subtopic.code}__{self.code}"


class FacetModel(BaseModel):
    """Facet model (lowest level)."""

    leaf = models.ForeignKey(
        LeafModel,
        on_delete=models.CASCADE,
        related_name='facets'
    )
    code = models.CharField(max_length=100, db_index=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    order_index = models.IntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    # Question metadata
    question_types = ArrayField(
        models.CharField(max_length=20),
        default=list,
        blank=True
    )
    difficulty_distribution = models.JSONField(default=dict)

    # Statistics
    total_questions = models.IntegerField(default=0)
    total_learners = models.IntegerField(default=0)
    average_mastery = models.FloatField(default=0.0)

    class Meta:
        db_table = 'facets'
        ordering = ['order_index', 'name']
        unique_together = [['leaf', 'code']]

    def __str__(self):
        return self.get_full_path()

    def get_full_path(self):
        """Get full content path."""
        return (
            f"{self.leaf.subtopic.topic.code}__"
            f"{self.leaf.subtopic.code}__"
            f"{self.leaf.code}__"
            f"{self.code}"
        )
