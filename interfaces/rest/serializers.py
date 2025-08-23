"""Django REST Framework serializers."""

from rest_framework import serializers
from infrastructure.persistence.models import (
    UserModel,
    QuestionModel,
    LearningSessionModel,
    FacetProgressModel
)


class UserSerializer(serializers.ModelSerializer):
    """User serializer."""

    class Meta:
        model = UserModel
        fields = [
            'id', 'email', 'username', 'full_name',
            'role', 'status', 'created_at', 'last_login_at'
        ]
        read_only_fields = ['id', 'created_at']


class QuestionSerializer(serializers.ModelSerializer):
    """Question serializer."""

    class Meta:
        model = QuestionModel
        fields = [
            'id', 'external_id', 'facet', 'type',
            'question', 'difficulty_level', 'source',
            'metadata', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class SessionSerializer(serializers.ModelSerializer):
    """Learning session serializer."""

    class Meta:
        model = LearningSessionModel
        fields = [
            'id', 'user', 'facet', 'status',
            'started_at', 'ended_at', 'metrics'
        ]
        read_only_fields = ['id', 'started_at']


class ProgressSerializer(serializers.ModelSerializer):
    """Progress serializer."""

    class Meta:
        model = FacetProgressModel
        fields = [
            'id', 'user', 'facet', 'mastery_score',
            'completion_percentage', 'accuracy_rate',
            'current_streak_days', 'last_activity_at'
        ]
        read_only_fields = ['id']