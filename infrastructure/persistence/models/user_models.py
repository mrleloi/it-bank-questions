"""User-related models."""

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import EmailValidator, MinLengthValidator
from .base import BaseModel, SoftDeleteModel


class UserManager(BaseUserManager):
    """Custom user manager."""

    def create_user(self, email, username, password=None, **extra_fields):
        """Create and save a regular user."""
        if not email:
            raise ValueError('Email is required')
        if not username:
            raise ValueError('Username is required')

        email = self.normalize_email(email)
        user = self.model(
            email=email,
            username=username,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        """Create and save a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('status', 'active')

        return self.create_user(email, username, password, **extra_fields)


class UserModel(AbstractBaseUser, PermissionsMixin, SoftDeleteModel):
    """User model."""

    ROLE_CHOICES = [
        ('learner', 'Learner'),
        ('moderator', 'Moderator'),
        ('admin', 'Admin'),
        ('guest', 'Guest'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('banned', 'Banned'),
    ]

    # Authentication fields
    email = models.EmailField(
        unique=True,
        validators=[EmailValidator()],
        db_index=True
    )
    username = models.CharField(
        max_length=50,
        unique=True,
        validators=[MinLengthValidator(3)],
        db_index=True
    )
    password = models.CharField(max_length=255)  # Will use Django's password hashing

    # Profile fields
    full_name = models.CharField(max_length=255, blank=True)
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='learner',
        db_index=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )

    # Verification
    email_verified_at = models.DateTimeField(null=True, blank=True)
    email_verification_token = models.CharField(max_length=100, blank=True)

    # Tracking
    last_login_at = models.DateTimeField(null=True, blank=True)
    last_activity_at = models.DateTimeField(null=True, blank=True)

    # Statistics
    total_study_time_seconds = models.IntegerField(default=0)
    total_questions_answered = models.IntegerField(default=0)
    current_streak_days = models.IntegerField(default=0)
    longest_streak_days = models.IntegerField(default=0)
    achievement_points = models.IntegerField(default=0)

    # Django admin
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['email', 'status']),
            models.Index(fields=['username', 'status']),
            models.Index(fields=['role', 'status']),
        ]

    def __str__(self):
        return f"{self.username} ({self.email})"

    def can_login(self):
        """Check if user can login."""
        return self.status == 'active' and not self.is_deleted

    def is_verified(self):
        """Check if email is verified."""
        return self.email_verified_at is not None


class UserPreferencesModel(BaseModel):
    """User preferences model."""

    user = models.OneToOneField(
        UserModel,
        on_delete=models.CASCADE,
        related_name='preferences'
    )

    # Display preferences
    theme = models.CharField(max_length=20, default='light')
    language = models.CharField(max_length=10, default='en')
    timezone = models.CharField(max_length=50, default='UTC')

    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    daily_reminder = models.BooleanField(default=True)
    reminder_time = models.TimeField(default='09:00')

    # Learning preferences
    daily_goal = models.IntegerField(default=20)
    auto_play_audio = models.BooleanField(default=False)
    show_timer = models.BooleanField(default=True)
    enable_hints = models.BooleanField(default=True)
    difficulty_preference = models.CharField(
        max_length=20,
        default='adaptive',
        choices=[
            ('adaptive', 'Adaptive'),
            ('easy', 'Easy'),
            ('medium', 'Medium'),
            ('hard', 'Hard'),
        ]
    )

    # Spaced repetition settings (JSON)
    review_settings = models.JSONField(default=dict)

    class Meta:
        db_table = 'user_preferences'
