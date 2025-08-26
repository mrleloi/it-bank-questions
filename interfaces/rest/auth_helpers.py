"""Authentication helpers and utilities for the REST API."""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from django.conf import settings
from django.contrib.auth import get_user_model
import jwt
from datetime import datetime, timedelta

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT token serializer with additional user info."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['user_id'] = user.id
        token['email'] = user.email
        token['role'] = user.role
        token['full_name'] = user.full_name

        return token

    def validate(self, attrs):
        """Validate and return token with user info."""
        data = super().validate(attrs)

        # Add user information to response
        user = self.user
        data.update({
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'full_name': user.full_name,
                'role': user.role,
                'status': user.status
            }
        })

        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom token obtain view with enhanced response."""
    serializer_class = CustomTokenObtainPairSerializer


# Authentication utility functions
def create_user_tokens(user):
    """Create access and refresh tokens for a user."""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


def decode_jwt_token(token):
    """Decode JWT token and return payload."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, 'Token has expired'
    except jwt.InvalidTokenError:
        return None, 'Invalid token'


# Authentication endpoints
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Login endpoint with JWT token generation.

    Expected payload:
    {
        "email": "user@example.com",
        "password": "password123"
    }
    """
    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return Response({
            'error': 'Email and password are required'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Find user by email
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({
            'error': 'Invalid credentials'
        }, status=status.HTTP_401_UNAUTHORIZED)

    # Check password
    if not user.check_password(password):
        return Response({
            'error': 'Invalid credentials'
        }, status=status.HTTP_401_UNAUTHORIZED)

    # Check if user is active
    if user.status != 'active':
        return Response({
            'error': 'Account is not active'
        }, status=status.HTTP_401_UNAUTHORIZED)

    # Generate tokens
    tokens = create_user_tokens(user)

    # Update last login
    user.last_login_at = datetime.now()
    user.save()

    return Response({
        'message': 'Login successful',
        'tokens': tokens,
        'user': {
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'full_name': user.full_name,
            'role': user.role,
            'status': user.status
        }
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """
    User registration endpoint.

    Expected payload:
    {
        "email": "user@example.com",
        "username": "username",
        "password": "password123",
        "full_name": "Full Name"
    }
    """
    email = request.data.get('email')
    username = request.data.get('username')
    password = request.data.get('password')
    full_name = request.data.get('full_name', '')

    # Validation
    if not email or not username or not password:
        return Response({
            'error': 'Email, username, and password are required'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Check if user already exists
    if User.objects.filter(email=email).exists():
        return Response({
            'error': 'User with this email already exists'
        }, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({
            'error': 'User with this username already exists'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Password validation
    if len(password) < 8:
        return Response({
            'error': 'Password must be at least 8 characters long'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Create user
    try:
        user = User.objects.create_user(
            email=email,
            username=username,
            password=password,
            full_name=full_name,
            role='student',  # Default role
            status='active'
        )

        # Generate tokens
        tokens = create_user_tokens(user)

        return Response({
            'message': 'Registration successful',
            'tokens': tokens,
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'full_name': user.full_name,
                'role': user.role,
                'status': user.status
            }
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            'error': f'Registration failed: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token_view(request):
    """
    Refresh JWT token endpoint.

    Expected payload:
    {
        "refresh": "refresh_token_here"
    }
    """
    refresh_token = request.data.get('refresh')

    if not refresh_token:
        return Response({
            'error': 'Refresh token is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        refresh = RefreshToken(refresh_token)
        access_token = refresh.access_token

        return Response({
            'access': str(access_token)
        })

    except Exception as e:
        return Response({
            'error': 'Invalid refresh token'
        }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
def logout_view(request):
    """
    Logout endpoint (blacklist refresh token).

    Expected payload:
    {
        "refresh": "refresh_token_here"
    }
    """
    refresh_token = request.data.get('refresh')

    if refresh_token:
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({
                'message': 'Logout successful'
            })
        except Exception:
            pass

    return Response({
        'message': 'Logout successful'
    })


@api_view(['GET'])
def verify_token_view(request):
    """
    Verify JWT token endpoint.
    Returns user info if token is valid.
    """
    user = request.user

    return Response({
        'valid': True,
        'user': {
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'full_name': user.full_name,
            'role': user.role,
            'status': user.status
        }
    })


# Development authentication helpers
@api_view(['POST'])
@permission_classes([AllowAny])
def dev_login_view(request):
    """
    Development login - creates a user if it doesn't exist.
    Only available in DEBUG mode.
    """
    if not settings.DEBUG:
        return Response({
            'error': 'This endpoint is only available in development mode'
        }, status=status.HTTP_403_FORBIDDEN)

    email = request.data.get('email', 'dev@example.com')
    password = request.data.get('password', 'devpassword')

    # Get or create user
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            'username': email.split('@')[0],
            'full_name': 'Development User',
            'role': 'student',
            'status': 'active'
        }
    )

    # Set password if user was created
    if created:
        user.set_password(password)
        user.save()

    # Generate tokens
    tokens = create_user_tokens(user)

    return Response({
        'message': 'Development login successful',
        'created': created,
        'tokens': tokens,
        'user': {
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'full_name': user.full_name,
            'role': user.role,
            'status': user.status
        }
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def auth_info_view(request):
    """
    Authentication information endpoint.
    """
    return Response({
        'authentication_methods': [
            'JWT Bearer Token',
            'Session Authentication (for admin)',
            'Basic Authentication (for development)'
        ],
        'endpoints': {
            'login': '/admin/api/auth/login/',
            'register': '/admin/api/auth/register/',
            'refresh': '/admin/api/auth/refresh/',
            'logout': '/admin/api/auth/logout/',
            'verify': '/admin/api/auth/verify/',
        },
        'dev_endpoints': {
            'dev_login': '/admin/api/auth/dev-login/' if settings.DEBUG else 'Not available in production'
        },
        'token_info': {
            'access_token_expire_minutes': settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
            'refresh_token_expire_days': settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS,
        },
        'headers': {
            'authorization': 'Bearer <access_token>',
            'content_type': 'application/json'
        },
        'example_usage': {
            'login': {
                'method': 'POST',
                'url': '/admin/api/auth/login/',
                'body': {
                    'email': 'user@example.com',
                    'password': 'password123'
                }
            },
            'authenticated_request': {
                'method': 'GET',
                'url': '/admin/api/users/me/',
                'headers': {
                    'Authorization': 'Bearer <access_token>'
                }
            }
        }
    })