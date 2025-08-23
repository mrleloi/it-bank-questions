"""Domain entities."""

from .base import Entity, AggregateRoot
from .user import User, UserPreferences, LearningSettings
from .question import Question, MCQOption, QuestionMetadata
from .learning_session import LearningSession, SessionStatus
from .spaced_repetition import SpacedRepetitionCard, CardStatistics
from .progress import UserProgress, FacetProgress
from .content_hierarchy import Topic, Subtopic, Leaf, Facet
from .learning_event import LearningEvent, EventType

__all__ = [
    'Entity',
    'AggregateRoot',
    'User',
    'UserPreferences',
    'LearningSettings',
    'Question',
    'MCQOption',
    'QuestionMetadata',
    'LearningSession',
    'SessionStatus',
    'SpacedRepetitionCard',
    'CardStatistics',
    'UserProgress',
    'FacetProgress',
    'Topic',
    'Subtopic',
    'Leaf',
    'Facet',
    'LearningEvent',
    'EventType',
]
