"""Content mapper."""

from typing import List, Dict, Any

from domain.entities import Topic, Subtopic, Leaf, Facet
from application.dto.response import ContentNodeResponse, ContentTreeResponse, ImportResultResponse


class ContentMapper:
    """Mapper for Content hierarchy entities and DTOs."""

    @staticmethod
    def topic_to_response_dto(topic: Topic) -> ContentNodeResponse:
        """Convert Topic entity to response DTO."""
        return ContentNodeResponse(
            id=topic.id,
            code=topic.code,
            name=topic.name,
            description=topic.description,
            level="topic",
            parent_id=None,
            total_questions=topic.total_questions,
            total_learners=topic.total_learners,
            average_mastery=topic.average_mastery
        )

    @staticmethod
    def subtopic_to_response_dto(subtopic: Subtopic) -> ContentNodeResponse:
        """Convert Subtopic entity to response DTO."""
        return ContentNodeResponse(
            id=subtopic.id,
            code=subtopic.code,
            name=subtopic.name,
            description=subtopic.description,
            level="subtopic",
            parent_id=subtopic.topic_id,
            total_questions=subtopic.total_questions,
            total_learners=subtopic.total_learners,
            average_mastery=subtopic.average_mastery
        )

    @staticmethod
    def leaf_to_response_dto(leaf: Leaf) -> ContentNodeResponse:
        """Convert Leaf entity to response DTO."""
        return ContentNodeResponse(
            id=leaf.id,
            code=leaf.code,
            name=leaf.name,
            description=leaf.description,
            level="leaf",
            parent_id=leaf.subtopic_id,
            total_questions=leaf.total_questions,
            total_learners=leaf.total_learners,
            average_mastery=leaf.average_mastery
        )

    @staticmethod
    def facet_to_response_dto(facet: Facet) -> ContentNodeResponse:
        """Convert Facet entity to response DTO."""
        return ContentNodeResponse(
            id=facet.id,
            code=facet.code,
            name=facet.name,
            description=facet.description,
            level="facet",
            parent_id=facet.leaf_id,
            total_questions=facet.total_questions,
            total_learners=facet.total_learners,
            average_mastery=facet.average_mastery,
            question_types=facet.question_types,
            difficulty_distribution=facet.difficulty_distribution
        )

    @staticmethod
    def to_tree_response(tree_data: Dict[str, Any]) -> ContentTreeResponse:
        """Convert tree data to ContentTreeResponse."""
        return ContentTreeResponse(
            nodes=tree_data['tree'],
            total_topics=tree_data['summary']['total_topics'],
            total_facets=tree_data['summary']['total_facets'],
            total_questions=tree_data['summary']['total_questions']
        )

    @staticmethod
    def to_import_result_response(
            imported: int,
            skipped: int,
            failed: int,
            errors: List[Dict[str, Any]],
            processing_time: float
    ) -> ImportResultResponse:
        """Create import result response."""
        return ImportResultResponse(
            imported=imported,
            skipped=skipped,
            failed=failed,
            errors=errors,
            processing_time_seconds=processing_time
        )