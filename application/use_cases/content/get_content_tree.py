"""Get content tree use case."""

from typing import Optional
from uuid import UUID

from domain.repositories import ContentRepository, ProgressRepository
from domain.value_objects import ContentLevel
from application.dto.request import GetContentTreeRequest
from application.dto.response import ContentTreeResponse
from application.mappers import ContentMapper


class GetContentTreeUseCase:
    """Use case for getting hierarchical content tree."""

    def __init__(
            self,
            content_repository: ContentRepository,
            progress_repository: Optional[ProgressRepository] = None
    ):
        self.content_repo = content_repository
        self.progress_repo = progress_repository

    async def execute(self, request: GetContentTreeRequest) -> ContentTreeResponse:
        """Get content tree with optional progress information."""
        # Validate request
        request.validate()

        # Get content tree from repository
        tree_data = await self.content_repo.get_content_tree(
            root_level=ContentLevel(request.root_level),
            root_id=request.root_id,
            max_depth=request.max_depth
        )

        # Add progress information if requested
        if request.include_progress and request.user_id and self.progress_repo:
            tree_data = await self._add_progress_info(tree_data, request.user_id)

        # Convert to response DTO
        return ContentMapper.to_tree_response(tree_data)

    async def _add_progress_info(self, tree_data: dict, user_id: UUID) -> dict:
        """Add user progress information to tree data."""
        try:
            # Get all user's facet progresses
            user_progress = await self.progress_repo.get_user_progress(user_id)
            facet_progresses = user_progress.facet_progresses if user_progress else {}

            # Recursively add progress to tree nodes
            tree_data['tree'] = await self._add_progress_to_nodes(
                tree_data['tree'], facet_progresses
            )

            return tree_data

        except Exception as e:
            # Log error but don't fail the request
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to add progress info: {e}")
            return tree_data

    async def _add_progress_to_nodes(self, nodes: list, facet_progresses: dict) -> list:
        """Recursively add progress information to nodes."""
        updated_nodes = []

        for node in nodes:
            # Add progress info for facets
            if node['level'] == 'facet':
                facet_id = UUID(node['id'])
                if facet_id in facet_progresses:
                    progress = facet_progresses[facet_id]
                    node['progress'] = {
                        'completion_percentage': progress.completion_percentage,
                        'mastery_score': progress.mastery_score,
                        'mastery_level': progress.mastery_level.value,
                        'accuracy_rate': progress.accuracy_rate,
                        'current_streak_days': progress.current_streak_days,
                        'last_activity_at': progress.last_activity_at.isoformat() if progress.last_activity_at else None
                    }
                else:
                    # No progress yet
                    node['progress'] = {
                        'completion_percentage': 0.0,
                        'mastery_score': 0.0,
                        'mastery_level': 'novice',
                        'accuracy_rate': 0.0,
                        'current_streak_days': 0,
                        'last_activity_at': None
                    }

            # Calculate aggregate progress for parent nodes
            elif node['level'] in ['topic', 'subtopic', 'leaf']:
                # Recursively process children first
                if 'children' in node:
                    node['children'] = await self._add_progress_to_nodes(
                        node['children'], facet_progresses
                    )
                    
                    # Calculate aggregate progress from children
                    node['progress'] = self._calculate_aggregate_progress(node['children'])

            updated_nodes.append(node)

        return updated_nodes

    def _calculate_aggregate_progress(self, children: list) -> dict:
        """Calculate aggregate progress from child nodes."""
        if not children:
            return {
                'completion_percentage': 0.0,
                'mastery_score': 0.0,
                'mastery_level': 'novice',
                'accuracy_rate': 0.0,
                'current_streak_days': 0,
                'last_activity_at': None
            }

        # Collect progress from children that have progress info
        child_progresses = [
            child.get('progress', {}) for child in children 
            if child.get('progress')
        ]

        if not child_progresses:
            return {
                'completion_percentage': 0.0,
                'mastery_score': 0.0,
                'mastery_level': 'novice',
                'accuracy_rate': 0.0,
                'current_streak_days': 0,
                'last_activity_at': None
            }

        # Calculate averages
        avg_completion = sum(p.get('completion_percentage', 0) for p in child_progresses) / len(child_progresses)
        avg_mastery = sum(p.get('mastery_score', 0) for p in child_progresses) / len(child_progresses)
        avg_accuracy = sum(p.get('accuracy_rate', 0) for p in child_progresses) / len(child_progresses)
        
        # Get max streak
        max_streak = max(p.get('current_streak_days', 0) for p in child_progresses)
        
        # Get most recent activity
        activities = [p.get('last_activity_at') for p in child_progresses if p.get('last_activity_at')]
        last_activity = max(activities) if activities else None

        # Determine aggregate mastery level
        mastery_level = 'novice'
        if avg_mastery >= 80:
            mastery_level = 'expert'
        elif avg_mastery >= 60:
            mastery_level = 'advanced'
        elif avg_mastery >= 40:
            mastery_level = 'intermediate'
        elif avg_mastery >= 20:
            mastery_level = 'beginner'

        return {
            'completion_percentage': avg_completion,
            'mastery_score': avg_mastery,
            'mastery_level': mastery_level,
            'accuracy_rate': avg_accuracy,
            'current_streak_days': max_streak,
            'last_activity_at': last_activity
        }