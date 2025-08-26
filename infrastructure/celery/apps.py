from django.apps.config import AppConfig


class CeleryConfig(AppConfig):
    """Configuration for the celery app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'infrastructure.celery'
    verbose_name = 'Celery App'
    label = 'celery'
    path = 'infrastructure/celery'
