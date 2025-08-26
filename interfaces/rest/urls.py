"""Complete URL configuration for Browsable API with web interface."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from django.conf import settings

# Import viewsets
try:
    from .views import (
        UserViewSet,
        QuestionViewSet,
        SessionViewSet,
        ProgressViewSet,
    )

    # Create router with custom base name
    router = DefaultRouter()
    router.register(r'users', UserViewSet, basename='user')
    router.register(r'questions', QuestionViewSet, basename='question')
    router.register(r'sessions', SessionViewSet, basename='session')
    router.register(r'progress', ProgressViewSet, basename='progress')

    # Enhanced API root with HTML template support
    @api_view(['GET'])
    @permission_classes([AllowAny])
    @renderer_classes([TemplateHTMLRenderer, JSONRenderer])
    def api_root(request, format=None):
        """
        # Learning Platform REST API

        Welcome to the Learning Platform REST API with browsable web interface.

        ## Available Endpoints:

        ### User Management
        - **Users**: Manage user accounts, profiles, and authentication
        - **My Profile**: View and update your personal profile
        - **User Statistics**: Admin dashboard for user metrics

        ### Content Management
        - **Questions**: Create and manage learning questions
        - **Bulk Import**: Import multiple questions at once
        - **Search & Filter**: Find questions by facet, difficulty, type

        ### Learning Tracking
        - **Sessions**: Track learning sessions and activities
        - **My Sessions**: View your personal learning history
        - **Progress**: Monitor learning progress across subjects

        ## Authentication

        This API supports multiple authentication methods:
        - **Session Authentication**: For web interface (login above)
        - **JWT Tokens**: For API access
        - **Basic Auth**: For development

        ## Features

        - **Web Interface**: Full CRUD operations through this browser interface
        - **JSON API**: All endpoints return JSON for programmatic access
        - **Filtering & Search**: Advanced filtering on all list endpoints
        - **Pagination**: Automatic pagination for large result sets
        - **Permissions**: Role-based access control
        """

        # For HTML requests, use template
        if request.accepted_renderer.format == 'html':
            return Response({
                'name': 'Learning Platform API',
                'description': 'Interactive REST API for Learning Platform',
                'user': request.user,
                'endpoints': [
                    {
                        'name': 'Users',
                        'url': request.build_absolute_uri('/admin/api/users/'),
                        'description': 'User management and profiles'
                    },
                    {
                        'name': 'Questions',
                        'url': request.build_absolute_uri('/admin/api/questions/'),
                        'description': 'Learning questions and content'
                    },
                    {
                        'name': 'Sessions',
                        'url': request.build_absolute_uri('/admin/api/sessions/'),
                        'description': 'Learning session tracking'
                    },
                    {
                        'name': 'Progress',
                        'url': request.build_absolute_uri('/admin/api/progress/'),
                        'description': 'Learning progress monitoring'
                    }
                ]
            }, template_name='api.html')

        # For JSON requests, return structured data
        base_url = request.build_absolute_uri('/admin/api/')

        return Response({
            'message': 'Learning Platform REST API',
            'version': '1.0',
            'documentation': f'{base_url}',
            'endpoints': {
                'users': {
                    'url': f'{base_url}users/',
                    'actions': ['list', 'create', 'retrieve', 'update', 'delete'],
                    'custom': {
                        'me': f'{base_url}users/me/',
                        'stats': f'{base_url}users/stats/'
                    }
                },
                'questions': {
                    'url': f'{base_url}questions/',
                    'actions': ['list', 'create', 'retrieve', 'update', 'delete'],
                    'custom': {
                        'by_facet': f'{base_url}questions/by_facet/?facet=<name>',
                        'bulk_import': f'{base_url}questions/bulk_import/',
                        'toggle_active': f'{base_url}questions/<id>/toggle_active/'
                    }
                },
                'sessions': {
                    'url': f'{base_url}sessions/',
                    'actions': ['list', 'retrieve'],
                    'custom': {
                        'my_sessions': f'{base_url}sessions/my_sessions/',
                        'stats': f'{base_url}sessions/stats/'
                    }
                },
                'progress': {
                    'url': f'{base_url}progress/',
                    'actions': ['list', 'retrieve', 'update'],
                    'custom': {
                        'my_progress': f'{base_url}progress/my_progress/',
                        'summary': f'{base_url}progress/summary/'
                    }
                }
            },
            'authentication': {
                'session': 'Use login form above',
                'token': 'POST /admin/api/auth/login/',
                'basic': 'For development only'
            }
        })

    main_urls = [
        path('', api_root, name='api-root'),
    ] + router.urls

except ImportError as e:
    print(f"Warning: Could not import browsable API views: {e}")

    @api_view(['GET'])
    @permission_classes([AllowAny])
    def fallback_root(request):
        return Response({
            'status': 'limited',
            'message': 'Browsable API views not available',
            'error': str(e)
        })

    main_urls = [
        path('', fallback_root, name='api-root-fallback'),
    ]

# Utility endpoints
@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint."""
    return Response({
        'status': 'healthy',
        'service': 'learning-platform-api',
        'browsable_api': True,
        'authenticated': request.user.is_authenticated,
        'user': request.user.username if request.user.is_authenticated else None
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def api_info(request):
    """API information with browsable interface details."""
    return Response({
        'name': 'Learning Platform REST API',
        'version': '1.0',
        'browsable_interface': True,
        'web_access': 'Available through this browser interface',
        'json_api': 'All endpoints support JSON for programmatic access',
        'authentication': {
            'web': 'Use login form in top navigation',
            'api': 'Send JWT token in Authorization header'
        },
        'features': [
            'Full CRUD operations through web interface',
            'JSON API for programmatic access',
            'Advanced filtering and search',
            'Automatic pagination',
            'Role-based permissions',
            'Interactive documentation'
        ]
    })

# URL patterns
urlpatterns = [
    # Authentication
    path('api-auth/', include('rest_framework.urls')),

    # Utility endpoints
    path('health/', health_check, name='health'),
    path('info/', api_info, name='info'),

    # Main API endpoints with browsable interface
    *main_urls,
]

# Add development endpoints
if settings.DEBUG:
    @api_view(['GET'])
    @permission_classes([AllowAny])
    def debug_info(request):
        """Debug information for development."""
        return Response({
            'debug_mode': True,
            'browsable_api': True,
            'user_authenticated': request.user.is_authenticated,
            'user_info': {
                'username': request.user.username,
                'email': request.user.email,
                'is_staff': request.user.is_staff,
                'is_superuser': request.user.is_superuser,
            } if request.user.is_authenticated else None,
            'request_info': {
                'method': request.method,
                'path': request.path,
                'format': request.accepted_renderer.format,
                'content_type': request.content_type,
            },
            'available_renderers': [
                'JSON (for API access)',
                'HTML (for web interface)',
            ],
            'tips': [
                'Use the web interface for easy CRUD operations',
                'Add ?format=json to any URL for JSON response',
                'Use the login form above to authenticate',
                'Try the different endpoints to see the browsable interface'
            ]
        })

    urlpatterns.append(path('debug/', debug_info, name='debug'))

# App name for namespacing
app_name = 'rest_api'