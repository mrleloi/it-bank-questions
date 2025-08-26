"""Content hierarchy entities."""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from uuid import UUID

from ..value_objects import ContentLevel, ContentPath
from ..exceptions import EntityValidationException
from .base import Entity


@dataclass
class ContentNode(Entity):
    """Base class for content hierarchy nodes."""

    code: str
    name: str
    description: Optional[str] = None
    level: ContentLevel = ContentLevel.TOPIC
    parent_id: Optional[UUID] = None
    order_index: int = 0
    is_active: bool = True

    # Statistics
    total_questions: int = 0
    total_learners: int = 0
    average_mastery: float = 0.0

    def validate(self) -> None:
        """Validate content node."""
        if not self.code or not self.code.strip():
            raise EntityValidationException("Code is required")

        if not self.name or not self.name.strip():
            raise EntityValidationException("Name is required")

        # Code should be lowercase alphanumeric with underscores
        if not self.code.replace('_', '').replace('-', '').isalnum():
            raise EntityValidationException(
                "Code can only contain letters, numbers, underscores, and hyphens"
            )

    def get_path_component(self) -> str:
        """Get this node's component for path building."""
        return self.code.lower()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = super().to_dict()
        data.update({
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'level': self.level.value,
            'parent_id': str(self.parent_id) if self.parent_id else None,
            'order_index': self.order_index,
            'is_active': self.is_active,
            'total_questions': self.total_questions,
            'total_learners': self.total_learners,
            'average_mastery': self.average_mastery,
        })
        return data


@dataclass
class Topic(ContentNode):
    """Topic level in hierarchy (e.g., backend_nodejs)."""

    level: ContentLevel = field(default=ContentLevel.TOPIC, init=False)
    icon: Optional[str] = None
    color: Optional[str] = None
    estimated_hours: Optional[int] = None

    def __post_init__(self):
        """Ensure level is set correctly."""
        self.level = ContentLevel.TOPIC
        super().__post_init__() if hasattr(super(), '__post_init__') else None


@dataclass
class Subtopic(ContentNode):
    """Subtopic level in hierarchy (e.g., api)."""

    level: ContentLevel = field(default=ContentLevel.SUBTOPIC, init=False)
    topic_id: Optional[UUID] = None

    def __post_init__(self):
        """Ensure level is set correctly."""
        self.level = ContentLevel.SUBTOPIC
        if self.topic_id:
            self.parent_id = self.topic_id
        super().__post_init__() if hasattr(super(), '__post_init__') else None

    def validate(self) -> None:
        """Validate subtopic."""
        super().validate()
        if not self.topic_id and not self.parent_id:
            raise EntityValidationException("Subtopic must have a parent topic")


@dataclass
class Leaf(ContentNode):
    """Leaf level in hierarchy (e.g., protocols)."""

    level: ContentLevel = field(default=ContentLevel.LEAF, init=False)
    subtopic_id: Optional[UUID] = None

    def __post_init__(self):
        """Ensure level is set correctly."""
        self.level = ContentLevel.LEAF
        if self.subtopic_id:
            self.parent_id = self.subtopic_id
        super().__post_init__() if hasattr(super(), '__post_init__') else None

    def validate(self) -> None:
        """Validate leaf."""
        super().validate()
        if not self.subtopic_id and not self.parent_id:
            raise EntityValidationException("Leaf must have a parent subtopic")


@dataclass
class Facet(ContentNode):
    """Facet level in hierarchy (e.g., graphql)."""

    level: ContentLevel = field(default=ContentLevel.FACET, init=False)
    leaf_id: Optional[UUID] = None

    # Facet-specific fields
    question_types: List[str] = field(default_factory=list)
    difficulty_distribution: Dict[int, int] = field(default_factory=dict)

    def __post_init__(self):
        """Ensure level is set correctly."""
        self.level = ContentLevel.FACET
        if self.leaf_id:
            self.parent_id = self.leaf_id
        super().__post_init__() if hasattr(super(), '__post_init__') else None

    def validate(self) -> None:
        """Validate facet."""
        super().validate()
        if not self.leaf_id and not self.parent_id:
            raise EntityValidationException("Facet must have a parent leaf")

    def update_statistics(self, question_type: str, difficulty: int) -> None:
        """Update facet statistics when a question is added."""
        if question_type not in self.question_types:
            self.question_types.append(question_type)

        if difficulty not in self.difficulty_distribution:
            self.difficulty_distribution[difficulty] = 0
        self.difficulty_distribution[difficulty] += 1

        self.total_questions += 1
        self.update_timestamp()

    def get_full_path(self) -> ContentPath:
        """Get full content path."""
        # This would need to traverse up the hierarchy
        # Simplified for now
        return ContentPath(
            topic="topic",
            subtopic="subtopic",
            leaf="leaf",
            facet=self.code
        )