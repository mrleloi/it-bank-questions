"""Improved Django REST Framework views with proper authentication and CRUD operations."""

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings
from django.contrib.auth import get_user_model

from infrastructure.persistence.models import *
from .serializers import *


# Custom permission for development mode
class IsAuthenticatedOrDevMode(IsAuthenticated):
    """Allow access in development mode without authentication."""

    def has_permission(self, request, view):
        if settings.DEBUG and settings.ENVIRONMENT == 'development':
            return True
        return super().has_permission(request, view)


class BaseViewSet(viewsets.ModelViewSet):
    """Base viewset with common configuration."""

    authentication_classes = [JWTAuthentication, SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticatedOrDevMode]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    def get_permissions(self):
        """Override permissions per action if needed."""
        if self.action in ['list', 'retrieve'] and settings.DEBUG:
            # Allow read operations in development
            self.permission_classes = [AllowAny]
        return [permission() for permission in self.permission_classes]


class UserViewSet(BaseViewSet):
    """Enhanced User management viewset."""

    queryset = UserModel.objects.all()
    serializer_class = UserSerializer
    search_fields = ['email', 'username', 'full_name']
    filterset_fields = ['role', 'status', 'is_active']
    ordering_fields = ['created_at', 'last_login_at', 'email']
    ordering = ['-created_at']

    def get_permissions(self):
        """Custom permissions for user operations."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser]
        elif self.action in ['list', 'retrieve']:
            if settings.DEBUG:
                self.permission_classes = [AllowAny]
            else:
                self.permission_classes = [IsAuthenticated]
        return [permission() for permission in self.permission_classes]

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticatedOrDevMode])
    def me(self, request):
        """Get current user profile."""
        if not request.user.is_authenticated and settings.DEBUG:
            # Return mock user for development
            return Response({
                'id': 1,
                'email': 'dev@example.com',
                'username': 'developer',
                'full_name': 'Development User',
                'role': 'student',
                'status': 'active'
            })

        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def suspend(self, request, pk=None):
        """Suspend user account."""
        user = self.get_object()
        user.status = 'suspended'
        user.save()
        return Response({'status': 'suspended', 'message': f'User {user.email} suspended'})

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def activate(self, request, pk=None):
        """Activate user account."""
        user = self.get_object()
        user.status = 'active'
        user.save()
        return Response({'status': 'activated', 'message': f'User {user.email} activated'})

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def stats(self, request):
        """Get user statistics."""
        total_users = UserModel.objects.count()
        active_users = UserModel.objects.filter(status='active').count()
        suspended_users = UserModel.objects.filter(status='suspended').count()

        return Response({
            'total_users': total_users,
            'active_users': active_users,
            'suspended_users': suspended_users,
            'students': UserModel.objects.filter(role='student').count(),
            'instructors': UserModel.objects.filter(role='instructor').count(),
        })


class QuestionViewSet(BaseViewSet):
    """Enhanced Question management viewset."""

    queryset = QuestionModel.objects.all()
    serializer_class = QuestionSerializer
    search_fields = ['question', 'external_id']
    filterset_fields = ['type', 'difficulty_level', 'source', 'is_active', 'facet']
    ordering_fields = ['created_at', 'difficulty_level']
    ordering = ['-created_at']

    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
    def bulk_import(self, request):
        """Bulk import questions."""
        # Get import data from request
        questions_data = request.data.get('questions', [])

        if not questions_data:
            return Response(
                {'error': 'No questions data provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        imported_count = 0
        errors = []

        for question_data in questions_data:
            try:
                serializer = self.get_serializer(data=question_data)
                if serializer.is_valid():
                    serializer.save()
                    imported_count += 1
                else:
                    errors.append({
                        'data': question_data,
                        'errors': serializer.errors
                    })
            except Exception as e:
                errors.append({
                    'data': question_data,
                    'errors': str(e)
                })

        return Response({
            'imported_count': imported_count,
            'total_provided': len(questions_data),
            'errors': errors
        })

    @action(detail=False, methods=['get'])
    def by_facet(self, request):
        """Get questions grouped by facet."""
        facet = request.query_params.get('facet')
        if not facet:
            return Response(
                {'error': 'Facet parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        questions = self.queryset.filter(facet=facet, is_active=True)
        serializer = self.get_serializer(questions, many=True)
        return Response({
            'facet': facet,
            'count': questions.count(),
            'questions': serializer.data
        })

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def toggle_active(self, request, pk=None):
        """Toggle question active status."""
        question = self.get_object()
        question.is_active = not question.is_active
        question.save()

        return Response({
            'status': 'active' if question.is_active else 'inactive',
            'message': f'Question {question.external_id} {"activated" if question.is_active else "deactivated"}'
        })


class SessionViewSet(BaseViewSet):
    """Enhanced Learning session viewset."""

    queryset = LearningSessionModel.objects.all()
    serializer_class = SessionSerializer
    filterset_fields = ['user', 'status', 'facet']
    ordering_fields = ['started_at', 'ended_at']
    ordering = ['-started_at']

    def get_queryset(self):
        """Filter by user if not admin."""
        queryset = super().get_queryset()

        # In development mode, return all sessions
        if settings.DEBUG and not self.request.user.is_authenticated:
            return queryset

        if not self.request.user.is_staff:
            return queryset.filter(user=self.request.user)
        return queryset

    @action(detail=False, methods=['get'])
    def my_sessions(self, request):
        """Get current user's sessions."""
        if settings.DEBUG and not request.user.is_authenticated:
            # Return mock data for development
            return Response({
                'sessions': [],
                'total': 0,
                'message': 'Development mode - no sessions'
            })

        sessions = self.queryset.filter(user=request.user)
        serializer = self.get_serializer(sessions, many=True)
        return Response({
            'sessions': serializer.data,
            'total': sessions.count()
        })

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def stats(self, request):
        """Get session statistics."""
        total_sessions = LearningSessionModel.objects.count()
        active_sessions = LearningSessionModel.objects.filter(status='active').count()
        completed_sessions = LearningSessionModel.objects.filter(status='completed').count()

        return Response({
            'total_sessions': total_sessions,
            'active_sessions': active_sessions,
            'completed_sessions': completed_sessions,
        })


class ProgressViewSet(BaseViewSet):
    """Enhanced Progress tracking viewset."""

    queryset = FacetProgressModel.objects.all()
    serializer_class = ProgressSerializer
    filterset_fields = ['user', 'facet']
    ordering_fields = ['mastery_score', 'completion_percentage', 'last_activity_at']
    ordering = ['-last_activity_at']

    def get_queryset(self):
        """Filter by user if not admin."""
        queryset = super().get_queryset()

        # In development mode, return all progress
        if settings.DEBUG and not self.request.user.is_authenticated:
            return queryset

        if not self.request.user.is_staff:
            return queryset.filter(user=self.request.user)
        return queryset

    @action(detail=False, methods=['get'])
    def my_progress(self, request):
        """Get current user's progress."""
        if settings.DEBUG and not request.user.is_authenticated:
            # Return mock data for development
            return Response({
                'progress': [],
                'total_facets': 0,
                'average_mastery': 0.0,
                'message': 'Development mode - no progress data'
            })

        progress = self.queryset.filter(user=request.user)
        serializer = self.get_serializer(progress, many=True)

        # Calculate statistics
        avg_mastery = 0
        if progress.exists():
            avg_mastery = sum(p.mastery_score for p in progress) / progress.count()

        return Response({
            'progress': serializer.data,
            'total_facets': progress.count(),
            'average_mastery': round(avg_mastery, 2)
        })

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get progress summary by facet."""
        facet = request.query_params.get('facet')

        queryset = self.get_queryset()
        if facet:
            queryset = queryset.filter(facet=facet)

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'facet': facet if facet else 'all',
            'progress_records': serializer.data,
            'count': queryset.count()
        })


# Additional API views for common operations
@api_view(['GET'])
@permission_classes([AllowAny])  # Always allow health check
def health_check(request):
    """REST API health check."""
    return Response({
        'status': 'healthy',
        'service': 'django-rest-framework',
        'message': 'REST endpoints are working',
        'debug_mode': settings.DEBUG,
        'environment': settings.ENVIRONMENT
    })


@api_view(['GET'])
@permission_classes([AllowAny if settings.DEBUG else IsAuthenticated])
def api_info(request):
    """API information endpoint."""
    return Response({
        'name': 'Learning Platform REST API',
        'version': '1.0',
        'endpoints': {
            'users': '/admin/api/users/',
            'questions': '/admin/api/questions/',
            'sessions': '/admin/api/sessions/',
            'progress': '/admin/api/progress/',
        },
        'authentication': 'JWT Token required (except in DEBUG mode)',
        'debug_mode': settings.DEBUG
    })