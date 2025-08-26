"""Base Django settings."""

import os
from pathlib import Path
import environ
from dotenv import load_dotenv

# Initialize environment variables
env = environ.Env()

# Try to read the ENVIRONMENT variable from the OS environment
load_dotenv('.env')
OS_ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
ENV_ENVIRONMENT_FILE = f'.env.{OS_ENVIRONMENT}'

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ROOT_DIR = BASE_DIR.parent

# Read .env file
environ.Env.read_env(os.path.join(ROOT_DIR, '.env'))
if os.path.exists(ENV_ENVIRONMENT_FILE):
    environ.Env.read_env(os.path.join(BASE_DIR, ENV_ENVIRONMENT_FILE))
    load_dotenv(ENV_ENVIRONMENT_FILE, override=True)

# ========================================
# CORE SETTINGS
# ========================================
SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
ENVIRONMENT = env('ENVIRONMENT')

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost'])

# ========================================
# APPLICATION DEFINITION
# ========================================
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'corsheaders',
    'django_celery_beat',
    'django_celery_results',
    'django_filters',
    'django_extensions',
]

LOCAL_APPS = [
    'infrastructure.persistence',
    'infrastructure.celery',
    'interfaces.rest',
    'interfaces.cli',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ========================================
# MIDDLEWARE
# ========================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

# ========================================
# TEMPLATES
# ========================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'
ASGI_APPLICATION = 'core.asgi.application'

# ========================================
# DATABASE
# ========================================
DATABASES = {
    'default': {
        'ENGINE': env('DB_ENGINE', default='django.db.backends.mysql'),
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT'),
        'CONN_MAX_AGE': env.int('DB_CONN_MAX_AGE', default=60),
        'OPTIONS': {
            'connect_timeout': 10,
            'max_connections': 100,
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        }
    }
}

# Use DATABASE_URL if provided
if env('DATABASE_URL', default=None):
    import dj_database_url
    DATABASES['default'] = dj_database_url.parse(
        env('DATABASE_URL'),
        conn_max_age=env.int('DB_CONN_MAX_AGE', default=60)
    )

# ========================================
# CACHE
# ========================================
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('CACHE_REDIS_URL', default='redis://127.0.0.1:6379/10'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'learning_platform_dev',
        'TIMEOUT': 300,  # 5 minutes for development
    }
}

# Cache TTL settings
CACHE_TTL = {
    'default': env.int('CACHE_TTL_DEFAULT', default=3600),
    'user': env.int('CACHE_TTL_USER', default=1800),
    'question': env.int('CACHE_TTL_QUESTION', default=7200),
    'progress': env.int('CACHE_TTL_PROGRESS', default=600),
}

# ========================================
# REDIS
# ========================================
REDIS_HOST = env('REDIS_HOST', default='localhost')
REDIS_PORT = env.int('REDIS_PORT', default=6379)
REDIS_DB = env.int('REDIS_DB', default=0)
REDIS_PASSWORD = env('REDIS_PASSWORD', default=None)

# ========================================
# CELERY
# ========================================
CELERY_BROKER_URL = env('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = env.int('CELERY_TASK_TIME_LIMIT', default=1800)
CELERY_TASK_SOFT_TIME_LIMIT = env.int('CELERY_TASK_SOFT_TIME_LIMIT', default=1500)
CELERY_WORKER_MAX_TASKS_PER_CHILD = env.int('CELERY_WORKER_MAX_TASKS_PER_CHILD', default=1000)
CELERY_RESULT_EXPIRES = 3600
CELERY_TASK_ROUTES = {
    'infrastructure.celery.tasks.*': {'queue': 'default'},
}
CELERY_WORKER_PREFETCH_MULTIPLIER = 1

# Development settings
if DEBUG:
    CELERY_TASK_ALWAYS_EAGER = env.bool('CELERY_TASK_ALWAYS_EAGER', default=False)
    CELERY_TASK_EAGER_PROPAGATES = True

# ========================================
# AUTHENTICATION
# ========================================
AUTH_USER_MODEL = 'persistence.UserModel'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': env.int('PASSWORD_MIN_LENGTH', default=8),
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# JWT Settings
JWT_SECRET_KEY = env('JWT_SECRET_KEY', default=SECRET_KEY)
JWT_ALGORITHM = env('JWT_ALGORITHM', default='HS256')
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = env.int('JWT_ACCESS_TOKEN_EXPIRE_MINUTES', default=30)
JWT_REFRESH_TOKEN_EXPIRE_DAYS = env.int('JWT_REFRESH_TOKEN_EXPIRE_DAYS', default=7)

# ========================================
# REST FRAMEWORK
# ========================================
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

# Session settings for admin login
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_COOKIE_NAME = 'learning_platform_sessionid'
SESSION_SAVE_EVERY_REQUEST = True

# Login URLs
LOGIN_URL = '/admin/login/'
LOGIN_REDIRECT_URL = '/admin/api/'
LOGOUT_REDIRECT_URL = '/admin/login/'

# Admin site settings
ADMIN_SITE_HEADER = 'Learning Platform Administration'
ADMIN_SITE_TITLE = 'Learning Platform Admin'
ADMIN_INDEX_TITLE = 'Welcome to Learning Platform Administration'

# ========================================
# CORS
# ========================================
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[])
CORS_ALLOW_CREDENTIALS = env.bool('CORS_ALLOW_CREDENTIALS', default=True)
CORS_ALLOW_ALL_ORIGINS = env.bool('CORS_ALLOW_ALL_ORIGINS', default=False)

if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True

# ========================================
# EMAIL
# ========================================
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', default='localhost')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('EMAIL_FROM_ADDRESS', default='noreply@learning-platform.com')

# ========================================
# STATIC & MEDIA FILES
# ========================================
STATIC_URL = env('STATIC_URL', default='/static/')
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Collect static files từ các app (bao gồm REST framework)
STATICFILES_DIRS = [
    BASE_DIR / 'static',  # Custom static files
]

# Static files finders
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

MEDIA_URL = env('MEDIA_URL', default='/media/')
MEDIA_ROOT = BASE_DIR / 'media'

# ========================================
# LOGGING
# ========================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': env('LOG_LEVEL', default='INFO'),
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': env('LOG_FILE', default='./logs/app.log'),
            'maxBytes': env.int('LOG_MAX_BYTES', default=10485760),
            'backupCount': env.int('LOG_BACKUP_COUNT', default=5),
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': [
            'console',
            # 'file',
        ],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': [
                'console',
                # 'file'
            ],
            'level': env('LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        # 'infrastructure': {
        #     'handlers': ['console', 'file'],
        #     'level': env('LOG_LEVEL', default='INFO'),
        #     'propagate': False,
        # },
        # 'application': {
        #     'handlers': ['console', 'file'],
        #     'level': env('LOG_LEVEL', default='INFO'),
        #     'propagate': False,
        # },
    },
}

# ========================================
# LEARNING SETTINGS
# ========================================
LEARNING_SETTINGS = {
    'daily_new_cards': env.int('DEFAULT_DAILY_NEW_CARDS', default=20),
    'daily_review_limit': env.int('DEFAULT_DAILY_REVIEW_LIMIT', default=100),
    'learning_steps': env.list('DEFAULT_LEARNING_STEPS', default=[1, 10], cast=int),
    'graduating_interval': env.int('DEFAULT_GRADUATING_INTERVAL', default=1),
    'easy_interval': env.int('DEFAULT_EASY_INTERVAL', default=4),
    'starting_ease': env.float('DEFAULT_STARTING_EASE', default=2.5),
    'easy_bonus': env.float('DEFAULT_EASY_BONUS', default=1.3),
    'interval_modifier': env.float('DEFAULT_INTERVAL_MODIFIER', default=1.0),
    'maximum_interval': env.int('DEFAULT_MAXIMUM_INTERVAL', default=36500),
    'leech_threshold': env.int('DEFAULT_LEECH_THRESHOLD', default=8),
}

# ========================================
# IMPORT SETTINGS
# ========================================
IMPORT_SETTINGS = {
    'batch_size': env.int('IMPORT_BATCH_SIZE', default=50),
    'parallel_workers': env.int('IMPORT_PARALLEL_WORKERS', default=4),
    'data_path': env('IMPORT_DATA_PATH', default='/app/data/questions'),
    'log_file': env('IMPORT_LOG_FILE', default='/app/logs/import.log'),
}

# ========================================
# FEATURE FLAGS
# ========================================
FEATURES = {
    'ai_hints': env.bool('FEATURE_AI_HINTS', default=False),
    'ai_evaluation': env.bool('FEATURE_AI_EVALUATION', default=False),
    'voice_interaction': env.bool('FEATURE_VOICE_INTERACTION', default=False),
    'multiplayer': env.bool('FEATURE_MULTIPLAYER', default=False),
    'offline_mode': env.bool('FEATURE_OFFLINE_MODE', default=False),
    'social_learning': env.bool('FEATURE_SOCIAL_LEARNING', default=False),
}

# ========================================
# INTERNATIONALIZATION
# ========================================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ========================================
# DEFAULT PRIMARY KEY
# ========================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Create staticfiles directory if not exists
if not (BASE_DIR / 'staticfiles').exists():
    os.makedirs(BASE_DIR / 'staticfiles', exist_ok=True)
