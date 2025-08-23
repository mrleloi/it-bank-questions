"""Content hierarchy value objects."""

from enum import Enum
from dataclasses import dataclass
from typing import List, Optional


class ContentLevel(str, Enum):
    """Levels in content hierarchy."""

    TOPIC = "topic"  # e.g., backend_nodejs
    SUBTOPIC = "subtopic"  # e.g., api
    LEAF = "leaf"  # e.g., protocols
    FACET = "facet"  # e.g., graphql

    def child_level(self) -> Optional['ContentLevel']:
        """Get the child level of this level."""
        mapping = {
            ContentLevel.TOPIC: ContentLevel.SUBTOPIC,
            ContentLevel.SUBTOPIC: ContentLevel.LEAF,
            ContentLevel.LEAF: ContentLevel.FACET,
            ContentLevel.FACET: None,
        }
        return mapping[self]

    def parent_level(self) -> Optional['ContentLevel']:
        """Get the parent level of this level."""
        mapping = {
            ContentLevel.TOPIC: None,
            ContentLevel.SUBTOPIC: ContentLevel.TOPIC,
            ContentLevel.LEAF: ContentLevel.SUBTOPIC,
            ContentLevel.FACET: ContentLevel.LEAF,
        }
        return mapping[self]

    def depth(self) -> int:
        """Get the depth of this level in hierarchy."""
        depths = {
            ContentLevel.TOPIC: 0,
            ContentLevel.SUBTOPIC: 1,
            ContentLevel.LEAF: 2,
            ContentLevel.FACET: 3,
        }
        return depths[self]


@dataclass(frozen=True)
class ContentPath:
    """Represents a path in content hierarchy."""

    topic: str
    subtopic: Optional[str] = None
    leaf: Optional[str] = None
    facet: Optional[str] = None

    @classmethod
    def from_string(cls, path_string: str) -> 'ContentPath':
        """Create from string like 'backend_nodejs__api__protocols__graphql'."""
        parts = path_string.split('__')
        return cls(
            topic=parts[0] if len(parts) > 0 else None,
            subtopic=parts[1] if len(parts) > 1 else None,
            leaf=parts[2] if len(parts) > 2 else None,
            facet=parts[3] if len(parts) > 3 else None,
        )

    def to_string(self) -> str:
        """Convert to string representation."""
        parts = [self.topic]
        if self.subtopic:
            parts.append(self.subtopic)
        if self.leaf:
            parts.append(self.leaf)
        if self.facet:
            parts.append(self.facet)
        return '__'.join(parts)

    def get_level(self) -> ContentLevel:
        """Get the deepest level of this path."""
        if self.facet:
            return ContentLevel.FACET
        elif self.leaf:
            return ContentLevel.LEAF
        elif self.subtopic:
            return ContentLevel.SUBTOPIC
        else:
            return ContentLevel.TOPIC

    def get_parent_path(self) -> Optional['ContentPath']:
        """Get parent path."""
        if self.facet:
            return ContentPath(self.topic, self.subtopic, self.leaf, None)
        elif self.leaf:
            return ContentPath(self.topic, self.subtopic, None, None)
        elif self.subtopic:
            return ContentPath(self.topic, None, None, None)
        else:
            return None

    def is_ancestor_of(self, other: 'ContentPath') -> bool:
        """Check if this path is an ancestor of another."""
        if self.topic != other.topic:
            return False
        if self.subtopic and self.subtopic != other.subtopic:
            return False
        if self.leaf and self.leaf != other.leaf:
            return False
        if self.facet and self.facet != other.facet:
            return False
        return True
