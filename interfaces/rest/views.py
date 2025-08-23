"""Django REST Framework views."""

from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend

from infrastructure.persistence.models import *
from .serializers import *


class UserViewSet(viewsets.ModelViewSet):
    """User management viewset."""

    queryset = UserModel.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['email', 'username', 'full_name']
    filterset_fields = ['role', 'status', 'is_active']

    @action(detail=True, methods=['post'])
    def suspend(self, request, pk=None):
        """Suspend user account."""
        user = self.get_object()
        user.status = 'suspended'
        user.save()
        return Response({'status': 'suspended'})

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate user account."""
        user = self.get_object()
        user.status = 'active'
        user.save()
        return Response({'status': 'activated'})


class QuestionViewSet(viewsets.ModelViewSet):
    """Question management viewset."""

    queryset = QuestionModel.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['question', 'external_id']
    filterset_fields = ['type', 'difficulty_level', 'source', 'is_active']

    @action(detail=False, methods=['post'])
    def bulk_import(self, request):
        """Bulk import questions."""
        # Implementation for bulk import
        return Response({'status': 'import started'})


class SessionViewSet(viewsets.ReadOnlyModelViewSet):
    """Learning session viewset."""

    queryset = LearningSessionModel.objects.all()
    serializer_class = SessionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user', 'status', 'facet']

    def get_queryset(self):
        """Filter by user if not admin."""
        if not self.request.user.is_staff:
            return self.queryset.filter(user=self.request.user)
        return self.queryset


class ProgressViewSet(viewsets.ReadOnlyModelViewSet):
    """Progress tracking viewset."""

    queryset = FacetProgressModel.objects.all()
    serializer_class = ProgressSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user', 'facet']

    def get_queryset(self):
        """Filter by user if not admin."""
        if not self.request.user.is_staff:
            return self.queryset.filter(user=self.request.user)
        return self.queryset
