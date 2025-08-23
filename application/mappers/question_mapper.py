"""Question mapper."""

from typing import List, Optional
from uuid import UUID, uuid4

from domain.entities import Question, MCQOption, QuestionMetadata
from domain.value_objects import QuestionType, QuestionSource, DifficultyLevel
from application.dto.response import QuestionResponse, MCQOptionResponse
from application.dto.request import CreateQuestionRequest


class QuestionMapper:
    """Mapper for Question entity and DTOs."""

    @staticmethod
    def to_response_dto(
            question: Question,
            card: Optional['SpacedRepetitionCard'] = None
    ) -> QuestionResponse:
        """Convert Question entity to response DTO."""
        options = None
        if question.is_mcq():
            options = [
                MCQOptionResponse(opt.key, opt.text)
                for opt in question.options
            ]

        response = QuestionResponse(
            id=question.id,
            type=question.type.value,
            question_text=question.question_text,
            difficulty_level=question.difficulty_level.value,
            estimated_time_seconds=question.get_estimated_time(),
            options=options,
            tags=question.metadata.tags,
            hints_available=len(question.metadata.hints) > 0
        )

        if card:
            response.card_state = card.state.value
            response.due_date = card.due_date
            response.ease_factor = card.ease_factor

        return response

    @staticmethod
    def from_create_request(
            request: CreateQuestionRequest,
            external_id: Optional[str] = None
    ) -> Question:
        """Create Question entity from create request."""
        # Build metadata
        metadata = QuestionMetadata(
            estimated_time_seconds=request.estimated_time_seconds,
            tags=request.tags
        )

        # Build MCQ options if applicable
        options = []
        if request.type == 'mcq' and request.options:
            for key, text in request.options.items():
                options.append(MCQOption(
                    key=key,
                    text=text,
                    is_correct=(key == request.correct_answer),
                    explanation=request.explanation if key == request.correct_answer else None
                ))

        return Question(
            id=uuid4(),
            external_id=external_id or str(uuid4()),
            facet_id=request.facet_id,
            type=QuestionType(request.type),
            question_text=request.question_text,
            difficulty_level=DifficultyLevel(request.difficulty_level),
            source=QuestionSource.USER_GENERATED,
            metadata=metadata,
            options=options,
            sample_answer=request.sample_answer
        )

    @staticmethod
    def from_import_data(data: dict, facet_id: UUID) -> Question:
        """Create Question entity from import data."""
        # Parse question type
        q_type = QuestionType(data['type'])

        # Build metadata
        metadata = QuestionMetadata(
            tags=data.get('tags', [])
        )

        # Build MCQ options if applicable
        options = []
        if q_type == QuestionType.MCQ and 'options' in data:
            for key, text in data['options'].items():
                options.append(MCQOption(
                    key=key,
                    text=text,
                    is_correct=(key == data.get('answer')),
                    explanation=data.get('explanation') if key == data.get('answer') else None
                ))

        return Question(
            id=uuid4(),
            external_id=data['id'],
            facet_id=facet_id,
            type=q_type,
            question_text=data['question'],
            difficulty_level=DifficultyLevel.MEDIUM,  # Default
            source=QuestionSource.HARD_RESOURCE,
            metadata=metadata,
            options=options,
            sample_answer=data.get('sample_answer')
        )