from django.apps.config import AppConfig


class PersistenceConfig(AppConfig):
    """Configuration for the persistence app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'infrastructure.persistence'
    verbose_name = 'Persistence Layer'
    label = 'persistence'
    path = 'infrastructure/persistence'
