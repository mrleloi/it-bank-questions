"""Simplified development settings to avoid Redis/Cache issues."""

from .base import *

# Override for development
DEBUG = True
ENVIRONMENT = 'development'

# Disable HTTPS requirements
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Django Debug Toolbar
try:
    import debug_toolbar
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    INTERNAL_IPS = ['127.0.0.1', 'localhost']
except ImportError:
    print("Debug toolbar not available")

# Simplified Cache for Development - Use local memory cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'learning-platform-dev-cache',
        'TIMEOUT': 300,  # 5 minutes
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
        }
    }
}

# Alternative: Try Redis with fallback
try:
    import redis
    redis_client = redis.Redis(host='127.0.0.1', port=6379, db=1, decode_responses=True)
    redis_client.ping()

    # Redis is available, use it with simplified config
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': 'redis://127.0.0.1:6379/1',
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            },
            'KEY_PREFIX': 'learning_dev',
            'TIMEOUT': 300,
        }
    }
    print("Using Redis cache for development")

except (ImportError, Exception) as e:
    print(f"Redis not available ({e}), using local memory cache")
    # Keep the local memory cache defined above

# Simplified Database - Use SQLite for development if MySQL not available
try:
    import MySQLdb  # or pymysql
    # Keep MySQL configuration from base.py
    print("Using MySQL database")
except ImportError:
    print("MySQL not available, using SQLite for development")
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db_development.sqlite3',
        }
    }

# Celery - Execute tasks synchronously in development
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Simplified Celery broker for development
CELERY_BROKER_URL = 'memory://'
CELERY_RESULT_BACKEND = 'cache+memory://'

# Email - Output to console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# CORS - Allow all origins in development
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',  # For browsable API
        'rest_framework.authentication.BasicAuthentication',  # For development
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',  # Web interface
        'rest_framework.renderers.AdminRenderer',  # Admin-style interface
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',  # For HTML forms
        'rest_framework.parsers.MultiPartParser',  # For file uploads
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': f"{env.int('RATE_LIMIT_PER_MINUTE', default=60)}/minute",
        'user': f"{env.int('RATE_LIMIT_PER_HOUR', default=1000)}/hour",
    },

    # Browsable API settings
    'DEFAULT_METADATA_CLASS': 'rest_framework.metadata.SimpleMetadata',
    'HTML_SELECT_CUTOFF': 1000,
    'HTML_SELECT_CUTOFF_TEXT': "More than {count} items...",

    # Exception handling
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',

    # Schema generation
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',

    # API versioning
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',

    # Content negotiation
    # 'DEFAULT_CONTENT_NEGOTIATION_CLASS': 'rest_framework.content_negotiation.DefaultContentNegotiation',
}

# Additional settings for better browsable API experience
if DEBUG:
    # In development, allow more permissive access for browsable API
    REST_FRAMEWORK.update({
        'DEFAULT_PERMISSION_CLASSES': [
            'rest_framework.permissions.IsAuthenticatedOrReadOnly',  # Allow read without auth
        ],
        'DEFAULT_THROTTLE_RATES': {
            'anon': '1000/minute',
            'user': '10000/hour',
        },
    })

# Development-specific logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'interfaces.rest': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Development feature flags
FEATURES.update({
    'dev_mode': True,
    'debug_api': True,
    'mock_data': True,
})

# JWT settings for development
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours for development
JWT_REFRESH_TOKEN_EXPIRE_DAYS = 30  # 30 days for development

print(f"Development settings loaded:")
print(f"- DEBUG: {DEBUG}")
print(f"- Database: {DATABASES['default']['ENGINE']}")
print(f"- Cache: {CACHES['default']['BACKEND']}")
print(f"- CORS Allow All: {CORS_ALLOW_ALL_ORIGINS}")