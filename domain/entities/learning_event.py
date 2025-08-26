"""Learning event entity for event sourcing."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from enum import Enum

from .base import Entity


class EventType(str, Enum):
    """Types of learning events."""

    # Session events
    SESSION_STARTED = "session_started"
    SESSION_COMPLETED = "session_completed"
    SESSION_ABANDONED = "session_abandoned"

    # Question events
    QUESTION_VIEWED = "question_viewed"
    QUESTION_ANSWERED = "question_answered"
    QUESTION_SKIPPED = "question_skipped"
    HINT_REQUESTED = "hint_requested"

    # Review events
    CARD_REVIEWED = "card_reviewed"
    CARD_SUSPENDED = "card_suspended"
    CARD_BURIED = "card_buried"

    # Progress events
    FACET_COMPLETED = "facet_completed"
    FACET_MASTERED = "facet_mastered"
    ACHIEVEMENT_UNLOCKED = "achievement_unlocked"
    STREAK_UPDATED = "streak_updated"

    # User events
    USER_REGISTERED = "user_registered"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    SETTINGS_UPDATED = "settings_updated"

    # Phase 2: AI events
    AI_HINT_GENERATED = "ai_hint_generated"
    AI_FEEDBACK_PROVIDED = "ai_feedback_provided"
    AI_CHAT_MESSAGE = "ai_chat_message"


@dataclass
class LearningEvent(Entity):
    """Learning event for analytics and event sourcing."""

    user_id: UUID
    event_type: EventType
    event_data: Dict[str, Any] = field(default_factory=dict)

    # Optional relations
    session_id: Optional[UUID] = None
    question_id: Optional[UUID] = None
    facet_id: Optional[UUID] = None

    # Metadata
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_type: Optional[str] = None

    def validate(self) -> None:
        """Validate event entity."""
        # Events are generally always valid as they represent facts
        pass

    def is_achievement_event(self) -> bool:
        """Check if this is an achievement event."""
        return self.event_type == EventType.ACHIEVEMENT_UNLOCKED

    def is_session_event(self) -> bool:
        """Check if this is a session event."""
        return self.event_type in {
            EventType.SESSION_STARTED,
            EventType.SESSION_COMPLETED,
            EventType.SESSION_ABANDONED
        }

    def is_question_event(self) -> bool:
        """Check if this is a question event."""
        return self.event_type in {
            EventType.QUESTION_VIEWED,
            EventType.QUESTION_ANSWERED,
            EventType.QUESTION_SKIPPED,
            EventType.HINT_REQUESTED
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = super().to_dict()
        data.update({
            'user_id': str(self.user_id),
            'event_type': self.event_type.value,
            'event_data': self.event_data,
            'session_id': str(self.session_id) if self.session_id else None,
            'question_id': str(self.question_id) if self.question_id else None,
            'facet_id': str(self.facet_id) if self.facet_id else None,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'device_type': self.device_type,
        })
        return data