"""Question repository implementation."""

from typing import Optional, List, Dict, Any
from uuid import UUID

from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist

from domain.entities import Question, MCQOption, QuestionMetadata
from domain.value_objects import QuestionType, DifficultyLevel, QuestionSource
from domain.repositories import QuestionRepository
from infrastructure.persistence.models import QuestionModel, MCQOptionModel
from .base import DjangoRepository


class DjangoQuestionRepository(DjangoRepository[Question, QuestionModel], QuestionRepository):
    """Django implementation of QuestionRepository."""

    def __init__(self, cache_manager=None):
        super().__init__(QuestionModel, cache_manager)

    async def get_by_external_id(self, external_id: str) -> Optional[Question]:
        """Get question by external ID."""
        try:
            model = await QuestionModel.objects.prefetch_related('mcq_options').aget(
                external_id=external_id
            )
            return await self._to_entity(model)
        except QuestionModel.DoesNotExist:
            return None

    async def get_by_facet(
            self,
            facet_id: UUID,
            question_type: Optional[QuestionType] = None,
            difficulty: Optional[DifficultyLevel] = None,
            limit: Optional[int] = None,
            offset: Optional[int] = None
    ) -> List[Question]:
        """Get questions by facet with filters."""
        queryset = QuestionModel.objects.filter(
            facet_id=facet_id,
            is_active=True
        ).prefetch_related('mcq_options')

        if question_type:
            queryset = queryset.filter(type=question_type.value)

        if difficulty:
            queryset = queryset.filter(difficulty_level=difficulty.value)

        if offset:
            queryset = queryset[offset:]
        if limit:
            queryset = queryset[:limit]

        models = [m async for m in queryset]
        return [await self._to_entity(m) for m in models]

    async def get_unanswered_by_user(
            self,
            user_id: UUID,
            facet_id: UUID,
            limit: Optional[int] = None
    ) -> List[Question]:
        """Get questions not answered by user."""
        # Get questions that user hasn't answered in this facet
        queryset = QuestionModel.objects.filter(
            facet_id=facet_id,
            is_active=True
        ).exclude(
            user_responses__user_id=user_id
        ).prefetch_related('mcq_options')

        if limit:
            queryset = queryset[:limit]

        models = [m async for m in queryset]
        return [await self._to_entity(m) for m in models]

    async def get_by_difficulty_range(
            self,
            facet_id: UUID,
            min_difficulty: int,
            max_difficulty: int,
            limit: Optional[int] = None
    ) -> List[Question]:
        """Get questions within difficulty range."""
        queryset = QuestionModel.objects.filter(
            facet_id=facet_id,
            difficulty_level__gte=min_difficulty,
            difficulty_level__lte=max_difficulty,
            is_active=True
        ).prefetch_related('mcq_options')

        if limit:
            queryset = queryset[:limit]

        models = [m async for m in queryset]
        return [await self._to_entity(m) for m in models]

    async def get_random_questions(
            self,
            facet_id: UUID,
            count: int,
            question_type: Optional[QuestionType] = None
    ) -> List[Question]:
        """Get random questions from facet."""
        queryset = QuestionModel.objects.filter(
            facet_id=facet_id,
            is_active=True
        ).prefetch_related('mcq_options')

        if question_type:
            queryset = queryset.filter(type=question_type.value)

        models = [m async for m in queryset.order_by('?')[:count]]
        return [await self._to_entity(m) for m in models]

    async def save(self, item: Question) -> Question:
        """Save or update a question."""
        model = self._to_model(item)
        await model.asave()

        # Save MCQ options if applicable
        if item.is_mcq() and item.options:
            # Delete existing options
            await MCQOptionModel.objects.filter(question=model).adelete()

            # Create new options
            option_models = []
            for option in item.options:
                option_model = MCQOptionModel(
                    question=model,
                    option_key=option.key,
                    option_text=option.text,
                    is_correct=option.is_correct,
                    explanation=option.explanation or ""
                )
                option_models.append(option_model)

            await MCQOptionModel.objects.abulk_create(option_models)

        return await self._to_entity(model)

    async def bulk_create(self, questions: List[Question]) -> List[Question]:
        """Bulk create questions."""
        question_models = []
        option_models = []

        # Create question models
        for question in questions:
            model = self._to_model(question)
            question_models.append(model)

        # Bulk create questions
        created_questions = await QuestionModel.objects.abulk_create(
            question_models
        )

        # Create MCQ options for MCQ questions
        for i, question in enumerate(questions):
            if question.is_mcq() and question.options:
                question_model = created_questions[i]
                for option in question.options:
                    option_model = MCQOptionModel(
                        question=question_model,
                        option_key=option.key,
                        option_text=option.text,
                        is_correct=option.is_correct,
                        explanation=option.explanation or ""
                    )
                    option_models.append(option_model)

        # Bulk create options
        if option_models:
            await MCQOptionModel.objects.abulk_create(option_models)

        # Return entities
        return [await self._to_entity(m) for m in created_questions]

    async def update_statistics(
            self,
            question_id: UUID,
            time_taken: int,
            is_correct: bool
    ) -> bool:
        """Update question statistics after answer."""
        try:
            question = await QuestionModel.objects.aget(id=question_id)
            question.update_statistics(is_correct, time_taken)
            await question.asave()
            return True
        except QuestionModel.DoesNotExist:
            return False

    async def get_statistics(self, question_id: UUID) -> Dict[str, Any]:
        """Get question statistics."""
        try:
            question = await QuestionModel.objects.aget(id=question_id)
            return {
                'times_answered': question.times_answered,
                'success_rate': question.success_rate,
                'average_time_seconds': question.average_time_seconds,
                'difficulty_level': question.difficulty_level,
            }
        except QuestionModel.DoesNotExist:
            return {}

    async def search_questions(
            self,
            query: str,
            facet_id: Optional[UUID] = None,
            limit: Optional[int] = None
    ) -> List[Question]:
        """Search questions by text."""
        queryset = QuestionModel.objects.filter(
            Q(question__icontains=query) |
            Q(external_id__icontains=query) |
            Q(tags__overlap=[query]),
            is_active=True
        ).prefetch_related('mcq_options')

        if facet_id:
            queryset = queryset.filter(facet_id=facet_id)

        if limit:
            queryset = queryset[:limit]

        models = [m async for m in queryset]
        return [await self._to_entity(m) for m in models]

    async def _to_entity(self, model: QuestionModel, load_relationship: bool = True) -> Question:
        """Convert QuestionModel to Question entity."""
        # Create metadata
        metadata = QuestionMetadata(
            estimated_time_seconds=model.estimated_time_seconds,
            tags=model.tags,
            hints=model.hints,
            references=model.references,
            learning_objectives=model.learning_objectives,
            prerequisites=model.prerequisites,
            ai_generated=model.ai_generated,
            ai_difficulty_assessment=model.ai_difficulty_assessment,
            community_rating=model.community_rating,
            times_answered=model.times_answered,
            average_time_seconds=model.average_time_seconds,
            success_rate=model.success_rate,
        )

        # Create MCQ options if applicable
        options = []
        if load_relationship and model.type == QuestionType.MCQ:
            async for opt_model in model.mcq_options.all():
                option = MCQOption(
                    key=opt_model.option_key,
                    text=opt_model.option_text,
                    is_correct=opt_model.is_correct,
                    explanation=opt_model.explanation
                )
                options.append(option)

        return Question(
            id=model.id,
            external_id=model.external_id,
            facet_id=model.facet_id,
            type=QuestionType(model.type),
            question_text=model.question,
            difficulty_level=DifficultyLevel(model.difficulty_level),
            source=QuestionSource(model.source),
            metadata=metadata,
            is_active=model.is_active,
            options=options,
            sample_answer=model.sample_answer,
            evaluation_criteria=model.evaluation_criteria,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def _to_model(self, entity: Question) -> QuestionModel:
        """Convert Question entity to QuestionModel."""
        return QuestionModel(
            id=entity.id,
            external_id=entity.external_id,
            facet_id=entity.facet_id,
            type=entity.type.value,
            question=entity.question_text,
            difficulty_level=entity.difficulty_level.value,
            source=entity.source.value,
            tags=entity.metadata.tags,
            estimated_time_seconds=entity.metadata.estimated_time_seconds,
            sample_answer=entity.sample_answer,
            evaluation_criteria=entity.evaluation_criteria,
            hints=entity.metadata.hints,
            references=entity.metadata.references,
            learning_objectives=entity.metadata.learning_objectives,
            prerequisites=entity.metadata.prerequisites,
            times_answered=entity.metadata.times_answered,
            times_correct=0,  # Will be calculated
            average_time_seconds=entity.metadata.average_time_seconds,
            success_rate=entity.metadata.success_rate,
            ai_generated=entity.metadata.ai_generated,
            ai_difficulty_assessment=entity.metadata.ai_difficulty_assessment,
            community_rating=entity.metadata.community_rating,
            is_active=entity.is_active,
        )