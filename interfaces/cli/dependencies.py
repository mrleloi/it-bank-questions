"""Django-specific helpers for accessing DI container."""

from typing import Optional
from infrastructure.container import Container, create_container

# Global container instance
_container: Optional[Container] = None


def get_django_container() -> Container:
    """Get container instance for Django environment."""
    global _container

    if _container is None:
        _container = create_container()

    return _container


# Direct access functions for Django commands
def get_json_importer():
    """Get JSON question importer for Django commands."""
    container = get_django_container()
    return container.json_importer()


def get_import_questions_use_case():
    """Get import questions use case for Django commands."""
    container = get_django_container()
    return container.import_questions_use_case()


def get_user_repository():
    """Get user repository for Django commands."""
    container = get_django_container()
    return container.user_repository()


def get_question_repository():
    """Get question repository for Django commands."""
    container = get_django_container()
    return container.question_repository()


def get_session_repository():
    """Get session repository for Django commands."""
    container = get_django_container()
    return container.session_repository()


def get_progress_repository():
    """Get progress repository for Django commands."""
    container = get_django_container()
    return container.progress_repository()


def get_content_repository():
    """Get content repository for Django commands."""
    container = get_django_container()
    return container.content_repository()


def get_event_repository():
    """Get event repository for Django commands."""
    container = get_django_container()
    return container.event_repository()


def get_spaced_repetition_repository():
    """Get spaced repetition repository for Django commands."""
    container = get_django_container()
    return container.spaced_repetition_repository()


# Service helpers
def get_spaced_repetition_service():
    """Get spaced repetition service for Django commands."""
    container = get_django_container()
    return container.spaced_repetition_service()


def get_learning_path_service():
    """Get learning path service for Django commands."""
    container = get_django_container()
    return container.learning_path_service()


def get_achievement_service():
    """Get achievement service for Django commands."""
    container = get_django_container()
    return container.achievement_service()


def get_analytics_service():
    """Get analytics service for Django commands."""
    container = get_django_container()
    return container.analytics_service()


# Email and event bus helpers
def get_email_service():
    """Get email service for Django commands."""
    container = get_django_container()
    return container.email_service()


def get_event_bus():
    """Get event bus for Django commands."""
    container = get_django_container()
    return container.event_bus()
