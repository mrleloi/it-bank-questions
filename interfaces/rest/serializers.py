from rest_framework import serializers
from django.contrib.auth import get_user_model
from infrastructure.persistence.models import (
    UserModel,
    QuestionModel,
    LearningSessionModel,
    FacetProgressModel
)


class UserSerializer(serializers.ModelSerializer):
    """User serializer with validation and computed fields."""

    full_name = serializers.CharField(max_length=255, required=False)
    password = serializers.CharField(write_only=True, required=False)
    confirm_password = serializers.CharField(write_only=True, required=False)

    # Computed fields
    session_count = serializers.SerializerMethodField()
    progress_count = serializers.SerializerMethodField()
    last_activity = serializers.SerializerMethodField()

    class Meta:
        model = UserModel
        fields = [
            'id', 'email', 'username', 'full_name',
            'role', 'status', 'is_active',
            'created_at', 'updated_at', 'last_login_at',
            'password', 'confirm_password',
            # Computed fields
            'session_count', 'progress_count', 'last_activity'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_login_at']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
        }

    def get_session_count(self, obj):
        """Get total number of sessions for this user."""
        return getattr(obj, 'learning_sessions', []).count() if hasattr(obj, 'learning_sessions') else 0

    def get_progress_count(self, obj):
        """Get number of progress records for this user."""
        return getattr(obj, 'facet_progress', []).count() if hasattr(obj, 'facet_progress') else 0

    def get_last_activity(self, obj):
        """Get last activity timestamp."""
        return obj.last_login_at or obj.updated_at

    def validate(self, data):
        """Validate user data."""
        # Password confirmation validation
        if 'password' in data:
            password = data.get('password')
            confirm_password = data.get('confirm_password')

            if password and password != confirm_password:
                raise serializers.ValidationError({
                    'confirm_password': 'Password confirmation does not match.'
                })

            # Password strength validation
            if password and len(password) < 8:
                raise serializers.ValidationError({
                    'password': 'Password must be at least 8 characters long.'
                })

        # Email domain validation (optional)
        if 'email' in data:
            email = data.get('email')
            if email and '@' not in email:
                raise serializers.ValidationError({
                    'email': 'Please enter a valid email address.'
                })

        return data

    def create(self, validated_data):
        """Create user with hashed password."""
        # Remove confirm_password from validated_data
        validated_data.pop('confirm_password', None)

        # Extract password
        password = validated_data.pop('password', None)

        # Create user
        user = UserModel.objects.create(**validated_data)

        # Set password if provided
        if password:
            user.set_password(password)
            user.save()

        return user

    def update(self, instance, validated_data):
        """Update user with password handling."""
        # Remove confirm_password from validated_data
        validated_data.pop('confirm_password', None)

        # Extract password
        password = validated_data.pop('password', None)

        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Update password if provided
        if password:
            instance.set_password(password)

        instance.save()
        return instance


class QuestionSerializer(serializers.ModelSerializer):
    """Question serializer with metadata validation."""

    # Optional nested serializers for related data
    answers = serializers.JSONField(required=False)
    explanation = serializers.CharField(max_length=1000, required=False, allow_blank=True)

    # Computed fields
    response_count = serializers.SerializerMethodField()
    average_difficulty = serializers.SerializerMethodField()

    class Meta:
        model = QuestionModel
        fields = [
            'id', 'external_id', 'facet', 'type',
            'question', 'answers', 'explanation',
            'difficulty_level', 'source', 'metadata',
            'is_active', 'created_at', 'updated_at',
            # Computed fields
            'response_count', 'average_difficulty'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_response_count(self, obj):
        """Get number of responses to this question."""
        # This would need to be implemented based on your response tracking
        return 0  # Placeholder

    def get_average_difficulty(self, obj):
        """Get average perceived difficulty from user responses."""
        # This would calculate based on user feedback
        return obj.difficulty_level  # Placeholder

    def validate_external_id(self, value):
        """Validate external_id uniqueness."""
        if value:
            # Check for duplicates excluding current instance
            queryset = QuestionModel.objects.filter(external_id=value)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise serializers.ValidationError(
                    f'Question with external_id "{value}" already exists.'
                )
        return value

    def validate_question(self, value):
        """Validate question text."""
        if not value or len(value.strip()) < 10:
            raise serializers.ValidationError(
                'Question must be at least 10 characters long.'
            )
        return value.strip()

    def validate_metadata(self, value):
        """Validate metadata structure."""
        if value and not isinstance(value, dict):
            raise serializers.ValidationError(
                'Metadata must be a valid JSON object.'
            )
        return value


class SessionSerializer(serializers.ModelSerializer):
    """Learning session serializer."""

    # User information
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)

    # Duration calculation
    duration_minutes = serializers.SerializerMethodField()
    questions_answered = serializers.SerializerMethodField()
    accuracy_rate = serializers.SerializerMethodField()

    class Meta:
        model = LearningSessionModel
        fields = [
            'id', 'user', 'user_email', 'user_name',
            'facet', 'status', 'started_at', 'ended_at',
            'metrics', 'created_at', 'updated_at',
            # Computed fields
            'duration_minutes', 'questions_answered', 'accuracy_rate'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'started_at']

    def get_duration_minutes(self, obj):
        """Calculate session duration in minutes."""
        if obj.started_at and obj.ended_at:
            duration = obj.ended_at - obj.started_at
            return round(duration.total_seconds() / 60, 2)
        return None

    def get_questions_answered(self, obj):
        """Get number of questions answered in this session."""
        metrics = obj.metrics or {}
        return metrics.get('questions_answered', 0)

    def get_accuracy_rate(self, obj):
        """Calculate accuracy rate for this session."""
        metrics = obj.metrics or {}
        correct = metrics.get('correct_answers', 0)
        total = metrics.get('total_answers', 0)
        return round((correct / total * 100), 2) if total > 0 else 0

    def validate(self, data):
        """Validate session data."""
        # Validate end time is after start time
        started_at = data.get('started_at')
        ended_at = data.get('ended_at')

        if started_at and ended_at and ended_at <= started_at:
            raise serializers.ValidationError({
                'ended_at': 'End time must be after start time.'
            })

        return data


class ProgressSerializer(serializers.ModelSerializer):
    """Progress serializer with user information."""

    # User information
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)

    # Computed fields
    mastery_level = serializers.SerializerMethodField()
    progress_trend = serializers.SerializerMethodField()
    last_activity_days_ago = serializers.SerializerMethodField()

    class Meta:
        model = FacetProgressModel
        fields = [
            'id', 'user', 'user_email', 'user_name',
            'facet', 'mastery_score', 'completion_percentage',
            'accuracy_rate', 'current_streak_days',
            'last_activity_at', 'created_at', 'updated_at',
            # Computed fields
            'mastery_level', 'progress_trend', 'last_activity_days_ago'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_mastery_level(self, obj):
        """Get descriptive mastery level."""
        score = obj.mastery_score
        if score >= 0.9:
            return 'Expert'
        elif score >= 0.7:
            return 'Advanced'
        elif score >= 0.5:
            return 'Intermediate'
        elif score >= 0.3:
            return 'Beginner'
        else:
            return 'Novice'

    def get_progress_trend(self, obj):
        """Calculate progress trend (simplified)."""
        # This would ideally compare with historical data
        accuracy = obj.accuracy_rate
        completion = obj.completion_percentage

        if accuracy >= 0.8 and completion >= 0.8:
            return 'Excellent'
        elif accuracy >= 0.6 and completion >= 0.6:
            return 'Good'
        elif accuracy >= 0.4 and completion >= 0.4:
            return 'Improving'
        else:
            return 'Needs Focus'

    def get_last_activity_days_ago(self, obj):
        """Calculate days since last activity."""
        if obj.last_activity_at:
            from django.utils import timezone
            delta = timezone.now() - obj.last_activity_at
            return delta.days
        return None

    def validate_mastery_score(self, value):
        """Validate mastery score range."""
        if value < 0 or value > 1:
            raise serializers.ValidationError(
                'Mastery score must be between 0 and 1.'
            )
        return value

    def validate_completion_percentage(self, value):
        """Validate completion percentage range."""
        if value < 0 or value > 100:
            raise serializers.ValidationError(
                'Completion percentage must be between 0 and 100.'
            )
        return value

    def validate_accuracy_rate(self, value):
        """Validate accuracy rate range."""
        if value < 0 or value > 1:
            raise serializers.ValidationError(
                'Accuracy rate must be between 0 and 1.'
            )
        return value


# Nested serializers for complex operations
class QuestionSummarySerializer(serializers.ModelSerializer):
    """Simplified question serializer for lists."""

    class Meta:
        model = QuestionModel
        fields = ['id', 'external_id', 'question', 'type', 'difficulty_level']


class UserSummarySerializer(serializers.ModelSerializer):
    """Simplified user serializer for nested relationships."""

    class Meta:
        model = UserModel
        fields = ['id', 'email', 'username', 'full_name', 'role']


class SessionSummarySerializer(serializers.ModelSerializer):
    """Simplified session serializer for lists."""

    duration_minutes = serializers.SerializerMethodField()

    class Meta:
        model = LearningSessionModel
        fields = ['id', 'facet', 'status', 'started_at', 'ended_at', 'duration_minutes']

    def get_duration_minutes(self, obj):
        """Calculate session duration in minutes."""
        if obj.started_at and obj.ended_at:
            duration = obj.ended_at - obj.started_at
            return round(duration.total_seconds() / 60, 2)
        return None


# Bulk operation serializers
class BulkQuestionImportSerializer(serializers.Serializer):
    """Serializer for bulk question import."""

    questions = QuestionSerializer(many=True)

    def validate_questions(self, value):
        """Validate questions list."""
        if not value:
            raise serializers.ValidationError("Questions list cannot be empty.")

        if len(value) > 1000:  # Reasonable limit
            raise serializers.ValidationError("Cannot import more than 1000 questions at once.")

        return value


class BulkUserOperationSerializer(serializers.Serializer):
    """Serializer for bulk user operations."""

    OPERATION_CHOICES = [
        ('activate', 'Activate'),
        ('suspend', 'Suspend'),
        ('delete', 'Delete'),
    ]

    user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        max_length=100
    )
    operation = serializers.ChoiceField(choices=OPERATION_CHOICES)

    def validate_user_ids(self, value):
        """Validate user IDs exist."""
        existing_ids = set(UserModel.objects.filter(id__in=value).values_list('id', flat=True))
        invalid_ids = set(value) - existing_ids

        if invalid_ids:
            raise serializers.ValidationError(
                f"Invalid user IDs: {list(invalid_ids)}"
            )

        return value


# Analytics serializers
class UserAnalyticsSerializer(serializers.Serializer):
    """Serializer for user analytics data."""

    total_sessions = serializers.IntegerField()
    total_questions_answered = serializers.IntegerField()
    average_accuracy = serializers.FloatField()
    current_streak = serializers.IntegerField()
    total_study_time_minutes = serializers.IntegerField()
    mastery_levels = serializers.DictField()
    progress_by_facet = serializers.DictField()
    recent_activity = serializers.ListField()


class SystemAnalyticsSerializer(serializers.Serializer):
    """Serializer for system-wide analytics."""

    total_users = serializers.IntegerField()
    active_users_today = serializers.IntegerField()
    active_users_week = serializers.IntegerField()
    total_questions = serializers.IntegerField()
    total_sessions_today = serializers.IntegerField()
    average_session_duration = serializers.FloatField()
    popular_facets = serializers.ListField()
    user_registrations_trend = serializers.DictField()


# Error response serializers
class ErrorResponseSerializer(serializers.Serializer):
    """Standard error response serializer."""

    error = serializers.CharField()
    message = serializers.CharField()
    details = serializers.DictField(required=False)
    timestamp = serializers.DateTimeField()


class ValidationErrorSerializer(serializers.Serializer):
    """Validation error response serializer."""

    field_errors = serializers.DictField()
    non_field_errors = serializers.ListField(required=False)


# Pagination serializers
class PaginatedResponseSerializer(serializers.Serializer):
    """Generic paginated response serializer."""

    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = serializers.ListField()


# Custom field serializers
class TimestampField(serializers.DateTimeField):
    """Custom timestamp field with timezone handling."""

    def to_representation(self, value):
        """Convert to ISO format with timezone."""
        if value:
            return value.isoformat()
        return None


class MetadataField(serializers.JSONField):
    """Custom metadata field with validation."""

    def to_internal_value(self, data):
        """Validate and convert metadata."""
        if data is None:
            return {}

        if isinstance(data, str):
            try:
                import json
                data = json.loads(data)
            except json.JSONDecodeError:
                raise serializers.ValidationError("Invalid JSON format")

        if not isinstance(data, dict):
            raise serializers.ValidationError("Metadata must be a JSON object")

        return data