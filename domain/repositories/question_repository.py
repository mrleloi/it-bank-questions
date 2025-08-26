"""Question repository interface."""

from abc import abstractmethod
from typing import Optional, List, Dict, Any
from uuid import UUID

from .base import Repository
from ..entities.question import Question
from ..value_objects import QuestionType, DifficultyLevel, QuestionSource


class QuestionRepository(Repository[Question]):
    """Repository for Question entity."""

    @abstractmethod
    async def get_by_external_id(self, external_id: str) -> Optional[Question]:
        """Get question by external ID."""
        pass

    @abstractmethod
    async def get_by_facet(
            self,
            facet_id: UUID,
            question_type: Optional[QuestionType] = None,
            difficulty: Optional[DifficultyLevel] = None,
            limit: Optional[int] = None,
            offset: Optional[int] = None
    ) -> List[Question]:
        """Get questions by facet with filters."""
        pass

    @abstractmethod
    async def get_unanswered_by_user(
            self,
            user_id: UUID,
            facet_id: UUID,
            limit: Optional[int] = None
    ) -> List[Question]:
        """Get questions not answered by user."""
        pass

    @abstractmethod
    async def get_by_difficulty_range(
            self,
            facet_id: UUID,
            min_difficulty: int,
            max_difficulty: int,
            limit: Optional[int] = None
    ) -> List[Question]:
        """Get questions within difficulty range."""
        pass

    @abstractmethod
    async def get_random_questions(
            self,
            facet_id: UUID,
            count: int,
            question_type: Optional[QuestionType] = None
    ) -> List[Question]:
        """Get random questions from facet."""
        pass

    @abstractmethod
    async def bulk_create(self, questions: List[Question]) -> List[Question]:
        """Bulk create questions."""
        pass

    @abstractmethod
    async def update_statistics(
            self,
            question_id: UUID,
            time_taken: int,
            is_correct: bool
    ) -> bool:
        """Update question statistics after answer."""
        pass

    @abstractmethod
    async def get_statistics(self, question_id: UUID) -> Dict[str, Any]:
        """Get question statistics."""
        pass

    @abstractmethod
    async def search_questions(
            self,
            query: str,
            facet_id: Optional[UUID] = None,
            limit: Optional[int] = None
    ) -> List[Question]:
        """Search questions by text."""
        pass