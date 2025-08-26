from django.apps.config import AppConfig


class CliConfig(AppConfig):
    """Configuration for the cli app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'interfaces.cli'
    verbose_name = 'Command Line Interface'
    label = 'cli'
    path = 'interfaces/cli'
