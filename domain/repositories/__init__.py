"""Repository interfaces."""

from .base import Repository, Specification
from .user_repository import UserRepository
from .question_repository import QuestionRepository
from .spaced_repetition_repository import SpacedRepetitionRepository
from .session_repository import SessionRepository
from .progress_repository import ProgressRepository
from .content_repository import ContentRepository
from .event_repository import EventRepository

__all__ = [
    'Repository',
    'Specification',
    'UserRepository',
    'QuestionRepository',
    'SpacedRepetitionRepository',
    'SessionRepository',
    'ProgressRepository',
    'ContentRepository',
    'EventRepository',
]