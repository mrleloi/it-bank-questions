"""Content-related request DTOs."""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from uuid import UUID


@dataclass
class ImportQuestionsRequest:
    """Import questions request."""

    file_path: str
    source: str = "hard_resource"
    dry_run: bool = False  # If true, validate without saving

    def validate(self) -> None:
        """Validate import request."""
        if not self.file_path:
            raise ValueError("File path is required")

        valid_sources = ['hard_resource', 'admin_imported', 'user_generated', 'ai_generated']
        if self.source not in valid_sources:
            raise ValueError(f"Invalid source: {self.source}")


@dataclass
class BulkImportRequest:
    """Bulk import multiple files request."""

    file_paths: List[str]
    source: str = "hard_resource"
    parallel: bool = True
    batch_size: int = 50

    def validate(self) -> None:
        """Validate bulk import."""
        if not self.file_paths:
            raise ValueError("At least one file path is required")

        if self.batch_size < 1 or self.batch_size > 1000:
            raise ValueError("Batch size must be between 1 and 1000")


@dataclass
class CreateQuestionRequest:
    """Create new question request."""

    facet_id: UUID
    type: str  # mcq, theory, scenario
    question_text: str
    difficulty_level: int = 3
    options: Optional[Dict[str, str]] = None  # For MCQ
    correct_answer: Optional[str] = None  # For MCQ
    explanation: Optional[str] = None
    sample_answer: Optional[str] = None  # For theory/scenario
    tags: List[str] = field(default_factory=list)
    estimated_time_seconds: Optional[int] = None

    def validate(self) -> None:
        """Validate question creation."""
        if not self.facet_id:
            raise ValueError("Facet ID is required")

        if self.type not in ['mcq', 'theory', 'scenario']:
            raise ValueError(f"Invalid question type: {self.type}")

        if not self.question_text:
            raise ValueError("Question text is required")

        if self.difficulty_level < 1 or self.difficulty_level > 5:
            raise ValueError("Difficulty level must be between 1 and 5")

        if self.type == 'mcq':
            if not self.options or len(self.options) < 2:
                raise ValueError("MCQ must have at least 2 options")

            if not self.correct_answer or self.correct_answer not in self.options:
                raise ValueError("MCQ must have a valid correct answer")


@dataclass
class SearchContentRequest:
    """Search content request."""

    query: str
    level: Optional[str] = None  # topic, subtopic, leaf, facet
    include_inactive: bool = False
    limit: int = 20

    def validate(self) -> None:
        """Validate search request."""
        if not self.query or len(self.query) < 2:
            raise ValueError("Search query must be at least 2 characters")

        if self.level and self.level not in ['topic', 'subtopic', 'leaf', 'facet']:
            raise ValueError(f"Invalid content level: {self.level}")

        if self.limit < 1 or self.limit > 100:
            raise ValueError("Limit must be between 1 and 100")


@dataclass
class GetContentTreeRequest:
    """Get content tree request."""

    root_level: str = "topic"  # Start level
    root_id: Optional[UUID] = None  # Specific node to start from
    max_depth: int = 4  # How deep to traverse
    include_stats: bool = True
    include_progress: bool = False
    user_id: Optional[UUID] = None  # Required if include_progress is True

    def validate(self) -> None:
        """Validate tree request."""
        if self.root_level not in ['topic', 'subtopic', 'leaf', 'facet']:
            raise ValueError(f"Invalid root level: {self.root_level}")

        if self.max_depth < 1 or self.max_depth > 4:
            raise ValueError("Max depth must be between 1 and 4")

        if self.include_progress and not self.user_id:
            raise ValueError("User ID is required when including progress")
