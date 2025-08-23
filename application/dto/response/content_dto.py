"""Content-related response DTOs."""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from uuid import UUID


@dataclass
class ContentNodeResponse:
    """Content node response."""

    id: UUID
    code: str
    name: str
    description: Optional[str]
    level: str  # topic, subtopic, leaf, facet
    parent_id: Optional[UUID]

    # Statistics
    total_questions: int
    total_learners: int
    average_mastery: float

    # For facets
    question_types: Optional[List[str]] = None
    difficulty_distribution: Optional[Dict[int, int]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = {
            'id': str(self.id),
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'level': self.level,
            'parent_id': str(self.parent_id) if self.parent_id else None,
            'statistics': {
                'total_questions': self.total_questions,
                'total_learners': self.total_learners,
                'average_mastery': self.average_mastery
            }
        }

        if self.question_types:
            data['question_types'] = self.question_types

        if self.difficulty_distribution:
            data['difficulty_distribution'] = self.difficulty_distribution

        return data


@dataclass
class ContentTreeResponse:
    """Content tree response."""

    nodes: List[Dict[str, Any]]
    total_topics: int
    total_facets: int
    total_questions: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'tree': self.nodes,
            'summary': {
                'total_topics': self.total_topics,
                'total_facets': self.total_facets,
                'total_questions': self.total_questions
            }
        }


@dataclass
class ImportResultResponse:
    """Import result response."""

    imported: int
    skipped: int
    failed: int
    errors: List[Dict[str, Any]]
    processing_time_seconds: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'result': {
                'imported': self.imported,
                'skipped': self.skipped,
                'failed': self.failed
            },
            'errors': self.errors,
            'processing_time_seconds': self.processing_time_seconds
        }
