from django.apps.config import AppConfig


class RestConfig(AppConfig):
    """Configuration for the rest app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'interfaces.rest'
    verbose_name = 'Rest API Interface'
    label = 'rest'
    path = 'interfaces/rest'
