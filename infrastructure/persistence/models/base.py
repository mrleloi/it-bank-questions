"""Base model classes."""

import uuid
from django.db import models
from django.utils import timezone


class BaseModel(models.Model):
    """Abstract base model with common fields."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        db_index=True
    )
    # objects = models.Manager()

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        """Override save to update timestamp."""
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)


class SoftDeleteModel(BaseModel):
    """Abstract model with soft delete support."""

    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def delete(self, soft=True, *args, **kwargs):
        """Soft delete by default."""
        if soft:
            self.is_deleted = True
            self.deleted_at = timezone.now()
            self.save()
        else:
            super().delete(*args, **kwargs)

    def restore(self):
        """Restore soft deleted object."""
        self.is_deleted = False
        self.deleted_at = None
        self.save()