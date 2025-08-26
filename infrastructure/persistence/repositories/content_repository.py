"""Content hierarchy repository implementation."""

from typing import Optional, List, Dict, Any
from uuid import UUID

from django.db.models import Q, Count
from django.db import transaction
from django.db.models.aggregates import Sum

from domain.entities import Topic, Subtopic, Leaf, Facet
from domain.value_objects import ContentLevel, ContentPath
from asgiref.sync import sync_to_async

from infrastructure.persistence.models import (
    TopicModel, SubtopicModel, LeafModel, FacetModel
)
from .base import DjangoRepository


class DjangoContentRepository(DjangoRepository[Facet, FacetModel]):
    """Django implementation of ContentRepository."""

    def __init__(self, cache_manager=None):
        super().__init__(FacetModel, cache_manager)

    async def get_topic(self, topic_id: UUID) -> Optional[Topic]:
        """Get topic by ID."""
        try:
            model = await TopicModel.objects.aget(id=topic_id)
            return self._topic_to_entity(model)
        except TopicModel.DoesNotExist:
            return None

    async def get_topic_by_code(self, code: str) -> Optional[Topic]:
        """Get topic by code."""
        try:
            model = await TopicModel.objects.aget(code=code)
            return self._topic_to_entity(model)
        except TopicModel.DoesNotExist:
            return None

    async def get_subtopic(self, subtopic_id: UUID) -> Optional[Subtopic]:
        """Get subtopic by ID."""
        try:
            model = await SubtopicModel.objects.select_related('topic').aget(id=subtopic_id)
            return self._subtopic_to_entity(model)
        except SubtopicModel.DoesNotExist:
            return None

    async def get_leaf(self, leaf_id: UUID) -> Optional[Leaf]:
        """Get leaf by ID."""
        try:
            model = await LeafModel.objects.select_related('subtopic__topic').aget(id=leaf_id)
            return self._leaf_to_entity(model)
        except LeafModel.DoesNotExist:
            return None

    async def get_facet(self, facet_id: UUID) -> Optional[Facet]:
        """Get facet by ID."""
        try:
            model = await FacetModel.objects.select_related('leaf__subtopic__topic').aget(id=facet_id)
            return self._facet_to_entity(model)
        except FacetModel.DoesNotExist:
            return None

    async def get_all_topics(self, active_only: bool = True) -> List[Topic]:
        """Get all topics."""
        queryset = TopicModel.objects.all()
        if active_only:
            queryset = queryset.filter(is_active=True)
        
        queryset = queryset.order_by('order_index', 'name')
        models = [m async for m in queryset]
        return [self._topic_to_entity(m) for m in models]

    async def get_subtopics_by_topic(
            self, 
            topic_id: UUID, 
            active_only: bool = True
    ) -> List[Subtopic]:
        """Get subtopics by topic."""
        queryset = SubtopicModel.objects.filter(topic_id=topic_id)
        if active_only:
            queryset = queryset.filter(is_active=True)
        
        queryset = queryset.order_by('order_index', 'name')
        models = [m async for m in queryset]
        return [self._subtopic_to_entity(m) for m in models]

    async def get_leaves_by_subtopic(
            self, 
            subtopic_id: UUID, 
            active_only: bool = True
    ) -> List[Leaf]:
        """Get leaves by subtopic."""
        queryset = LeafModel.objects.filter(subtopic_id=subtopic_id)
        if active_only:
            queryset = queryset.filter(is_active=True)
        
        queryset = queryset.order_by('order_index', 'name')
        models = [m async for m in queryset]
        return [self._leaf_to_entity(m) for m in models]

    async def get_facets_by_leaf(
            self, 
            leaf_id: UUID, 
            active_only: bool = True
    ) -> List[Facet]:
        """Get facets by leaf."""
        queryset = FacetModel.objects.filter(leaf_id=leaf_id)
        if active_only:
            queryset = queryset.filter(is_active=True)
        
        queryset = queryset.order_by('order_index', 'name')
        models = [m async for m in queryset]
        return [self._facet_to_entity(m) for m in models]

    async def search_content(
            self, 
            query: str, 
            level: Optional[ContentLevel] = None,
            limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Search content across all levels."""
        results = []

        # Search topics
        if not level or level == ContentLevel.TOPIC:
            topic_queryset = TopicModel.objects.filter(
                Q(name__icontains=query) | Q(code__icontains=query),
                is_active=True
            )
            if limit:
                topic_queryset = topic_queryset[:limit//4 if level else limit]
            
            async for topic in topic_queryset:
                results.append({
                    'id': topic.id,
                    'level': 'topic',
                    'code': topic.code,
                    'name': topic.name,
                    'description': topic.description,
                    'path': topic.code
                })

        # Search subtopics
        if not level or level == ContentLevel.SUBTOPIC:
            subtopic_queryset = SubtopicModel.objects.select_related('topic').filter(
                Q(name__icontains=query) | Q(code__icontains=query),
                is_active=True
            )
            if limit:
                subtopic_queryset = subtopic_queryset[:limit//4 if level else limit]
            
            async for subtopic in subtopic_queryset:
                results.append({
                    'id': subtopic.id,
                    'level': 'subtopic',
                    'code': subtopic.code,
                    'name': subtopic.name,
                    'description': subtopic.description,
                    'path': f"{subtopic.topic.code}__{subtopic.code}"
                })

        # Search leaves
        if not level or level == ContentLevel.LEAF:
            leaf_queryset = LeafModel.objects.select_related('subtopic__topic').filter(
                Q(name__icontains=query) | Q(code__icontains=query),
                is_active=True
            )
            if limit:
                leaf_queryset = leaf_queryset[:limit//4 if level else limit]
            
            async for leaf in leaf_queryset:
                results.append({
                    'id': leaf.id,
                    'level': 'leaf',
                    'code': leaf.code,
                    'name': leaf.name,
                    'description': leaf.description,
                    'path': f"{leaf.subtopic.topic.code}__{leaf.subtopic.code}__{leaf.code}"
                })

        # Search facets
        if not level or level == ContentLevel.FACET:
            facet_queryset = FacetModel.objects.select_related('leaf__subtopic__topic').filter(
                Q(name__icontains=query) | Q(code__icontains=query),
                is_active=True
            )
            if limit:
                facet_queryset = facet_queryset[:limit//4 if level else limit]
            
            async for facet in facet_queryset:
                results.append({
                    'id': facet.id,
                    'level': 'facet',
                    'code': facet.code,
                    'name': facet.name,
                    'description': facet.description,
                    'path': facet.get_full_path()
                })

        return results[:limit] if limit else results

    @sync_to_async
    def _create_hierarchy_atomic(
            self,
            topic_code: str,
            subtopic_code: str,
            leaf_code: str,
            facet_code: str
    ) -> FacetModel:
        """Create hierarchy atomically in sync context."""
        with transaction.atomic():
            # Get or create topic
            topic, _ = TopicModel.objects.get_or_create(
                code=topic_code,
                defaults={
                    'name': topic_code.replace('_', ' ').title(),
                    'description': f"Topic: {topic_code}"
                }
            )

            # Get or create subtopic
            subtopic, _ = SubtopicModel.objects.get_or_create(
                topic=topic,
                code=subtopic_code,
                defaults={
                    'name': subtopic_code.replace('_', ' ').title(),
                    'description': f"Subtopic: {subtopic_code}"
                }
            )

            # Get or create leaf
            leaf, _ = LeafModel.objects.get_or_create(
                subtopic=subtopic,
                code=leaf_code,
                defaults={
                    'name': leaf_code.replace('_', ' ').title(),
                    'description': f"Leaf: {leaf_code}"
                }
            )

            # Get or create facet
            facet, _ = FacetModel.objects.get_or_create(
                leaf=leaf,
                code=facet_code,
                defaults={
                    'name': facet_code.replace('_', ' ').title(),
                    'description': f"Facet: {facet_code}"
                }
            )

            return facet

    async def ensure_hierarchy(
            self,
            topic_code: str,
            subtopic_code: str,
            leaf_code: str,
            facet_code: str
    ) -> Facet:
        """Ensure complete hierarchy exists, create if missing."""
        facet_model = await self._create_hierarchy_atomic(
            topic_code, subtopic_code, leaf_code, facet_code
        )
        return self._facet_to_entity(facet_model)

    async def get_content_tree(
            self,
            root_level: ContentLevel = ContentLevel.TOPIC,
            root_id: Optional[UUID] = None,
            max_depth: int = 4
    ) -> Dict[str, Any]:
        """Get hierarchical content tree."""
        if root_level == ContentLevel.TOPIC:
            if root_id:
                topics = [await TopicModel.objects.aget(id=root_id)]
            else:
                topics = [t async for t in TopicModel.objects.filter(is_active=True).order_by('order_index')]
        else:
            # Handle other root levels
            topics = []

        tree_data = []
        for topic in topics:
            topic_data = {
                'id': str(topic.id),
                'level': 'topic',
                'code': topic.code,
                'name': topic.name,
                'description': topic.description,
                'statistics': {
                    'total_questions': topic.total_questions,
                    'total_learners': topic.total_learners,
                    'average_mastery': topic.average_mastery
                },
                'children': []
            }

            if max_depth > 1:
                subtopics = [s async for s in topic.subtopics.filter(is_active=True).order_by('order_index')]
                for subtopic in subtopics:
                    subtopic_data = {
                        'id': str(subtopic.id),
                        'level': 'subtopic',
                        'code': subtopic.code,
                        'name': subtopic.name,
                        'description': subtopic.description,
                        'statistics': {
                            'total_questions': subtopic.total_questions,
                            'total_learners': subtopic.total_learners,
                            'average_mastery': subtopic.average_mastery
                        },
                        'children': []
                    }

                    if max_depth > 2:
                        leaves = [l async for l in subtopic.leaves.filter(is_active=True).order_by('order_index')]
                        for leaf in leaves:
                            leaf_data = {
                                'id': str(leaf.id),
                                'level': 'leaf',
                                'code': leaf.code,
                                'name': leaf.name,
                                'description': leaf.description,
                                'statistics': {
                                    'total_questions': leaf.total_questions,
                                    'total_learners': leaf.total_learners,
                                    'average_mastery': leaf.average_mastery
                                },
                                'children': []
                            }

                            if max_depth > 3:
                                facets = [f async for f in leaf.facets.filter(is_active=True).order_by('order_index')]
                                for facet in facets:
                                    facet_data = {
                                        'id': str(facet.id),
                                        'level': 'facet',
                                        'code': facet.code,
                                        'name': facet.name,
                                        'description': facet.description,
                                        'question_types': facet.question_types,
                                        'difficulty_distribution': facet.difficulty_distribution,
                                        'statistics': {
                                            'total_questions': facet.total_questions,
                                            'total_learners': facet.total_learners,
                                            'average_mastery': facet.average_mastery
                                        }
                                    }
                                    leaf_data['children'].append(facet_data)

                            subtopic_data['children'].append(leaf_data)

                    topic_data['children'].append(subtopic_data)

            tree_data.append(topic_data)

        # Calculate summary statistics
        total_topics = len(tree_data)
        total_facets = await FacetModel.objects.filter(is_active=True).acount()
        total_questions = await FacetModel.objects.filter(is_active=True).aaggregate(
            total=Sum('total_questions')
        )['total'] or 0

        return {
            'tree': tree_data,
            'summary': {
                'total_topics': total_topics,
                'total_facets': total_facets,
                'total_questions': total_questions
            }
        }

    def _topic_to_entity(self, model: TopicModel) -> Topic:
        """Convert TopicModel to Topic entity."""
        return Topic(
            id=model.id,
            code=model.code,
            name=model.name,
            description=model.description,
            icon=model.icon,
            color=model.color,
            order_index=model.order_index,
            is_active=model.is_active,
            total_questions=model.total_questions,
            total_learners=model.total_learners,
            average_mastery=model.average_mastery,
            estimated_hours=model.estimated_hours,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def _subtopic_to_entity(self, model: SubtopicModel) -> Subtopic:
        """Convert SubtopicModel to Subtopic entity."""
        return Subtopic(
            id=model.id,
            code=model.code,
            name=model.name,
            description=model.description,
            order_index=model.order_index,
            is_active=model.is_active,
            total_questions=model.total_questions,
            total_learners=model.total_learners,
            average_mastery=model.average_mastery,
            topic_id=model.topic_id,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def _leaf_to_entity(self, model: LeafModel) -> Leaf:
        """Convert LeafModel to Leaf entity."""
        return Leaf(
            id=model.id,
            code=model.code,
            name=model.name,
            description=model.description,
            order_index=model.order_index,
            is_active=model.is_active,
            total_questions=model.total_questions,
            total_learners=model.total_learners,
            average_mastery=model.average_mastery,
            subtopic_id=model.subtopic_id,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def _facet_to_entity(self, model: FacetModel) -> Facet:
        """Convert FacetModel to Facet entity."""
        return Facet(
            id=model.id,
            code=model.code,
            name=model.name,
            description=model.description,
            order_index=model.order_index,
            is_active=model.is_active,
            question_types=model.question_types,
            difficulty_distribution=model.difficulty_distribution,
            total_questions=model.total_questions,
            total_learners=model.total_learners,
            average_mastery=model.average_mastery,
            leaf_id=model.leaf_id,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def _to_entity(self, model: FacetModel) -> Facet:
        """Convert model to entity."""
        return self._facet_to_entity(model)

    def _to_model(self, entity: Facet) -> FacetModel:
        """Convert entity to model."""
        return FacetModel(
            id=entity.id,
            leaf_id=entity.leaf_id,
            code=entity.code,
            name=entity.name,
            description=entity.description,
            order_index=entity.order_index,
            is_active=entity.is_active,
            question_types=entity.question_types,
            difficulty_distribution=entity.difficulty_distribution,
            total_questions=entity.total_questions,
            total_learners=entity.total_learners,
            average_mastery=entity.average_mastery
        )