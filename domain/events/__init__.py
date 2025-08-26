"""Domain events."""

from .base import DomainEvent, UserDomainEvent, LearningDomainEvent

# User events
from .user_events import (
    UserRegisteredEvent,
    UserLoggedInEvent,
    UserLoggedOutEvent,
    UserEmailVerifiedEvent,
    UserPasswordResetEvent,
    UserProfileUpdatedEvent,
    UserPreferencesUpdatedEvent,
    UserSuspendedEvent,
    UserActivatedEvent,
    UserDeletedEvent
)

# Learning events
from .learning_events import (
    SessionStartedEvent,
    SessionCompletedEvent,
    SessionAbandonedEvent,
    QuestionAnsweredEvent,
    QuestionViewedEvent,
    HintRequestedEvent,
    CardReviewedEvent,
    FacetCompletedEvent,
    FacetMasteredEvent,
    StreakUpdatedEvent,
    AchievementUnlockedEvent,
    LearningGoalSetEvent,
    LearningGoalAchievedEvent
)

__all__ = [
    # Base classes
    'DomainEvent',
    'UserDomainEvent', 
    'LearningDomainEvent',
    
    # User events
    'UserRegisteredEvent',
    'UserLoggedInEvent',
    'UserLoggedOutEvent',
    'UserEmailVerifiedEvent',
    'UserPasswordResetEvent',
    'UserProfileUpdatedEvent',
    'UserPreferencesUpdatedEvent',
    'UserSuspendedEvent',
    'UserActivatedEvent',
    'UserDeletedEvent',
    
    # Learning events
    'SessionStartedEvent',
    'SessionCompletedEvent',
    'SessionAbandonedEvent',
    'QuestionAnsweredEvent',
    'QuestionViewedEvent',
    'HintRequestedEvent',
    'CardReviewedEvent',
    'FacetCompletedEvent',
    'FacetMasteredEvent',
    'StreakUpdatedEvent',
    'AchievementUnlockedEvent',
    'LearningGoalSetEvent',
    'LearningGoalAchievedEvent',
]