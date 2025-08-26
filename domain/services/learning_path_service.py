"""Learning path service."""

import random
from typing import List, Optional, Dict, Any
from uuid import UUID

from ..entities import Question, LearningSession, UserProgress, FacetProgress
from ..repositories import QuestionRepository, ProgressRepository, SpacedRepetitionRepository, ContentRepository
from ..value_objects import QuestionType, DifficultyLevel


class LearningPathService:
    """Service for adaptive learning path generation."""

    def __init__(
            self,
            question_repo: QuestionRepository,
            progress_repo: ProgressRepository,
            sr_repo: SpacedRepetitionRepository,
            content_repo: ContentRepository
    ):
        self.question_repo = question_repo
        self.progress_repo = progress_repo
        self.sr_repo = sr_repo
        self.content_repo = content_repo

    async def get_adaptive_questions(
            self,
            user_id: UUID,
            facet_id: UUID,
            session: LearningSession,
            count: int = 20
    ) -> List[Question]:
        """Get adaptive questions based on user's progress and preferences."""
        # Get user's progress for this facet
        facet_progress = await self.progress_repo.get_facet_progress(user_id, facet_id)
        
        # Determine optimal difficulty range
        difficulty_range = await self._calculate_optimal_difficulty(
            user_id, facet_id, facet_progress
        )
        
        # Get mix of question types based on session preferences
        question_types = session.question_types if session.question_types else ['mcq', 'theory', 'scenario']
        
        # Calculate question distribution
        distribution = await self._calculate_question_distribution(
            user_id, facet_id, question_types, count
        )
        
        selected_questions = []
        
        # Get questions by type and difficulty
        for q_type, type_count in distribution.items():
            if type_count == 0:
                continue
                
            questions = await self._get_questions_by_criteria(
                user_id=user_id,
                facet_id=facet_id,
                question_type=QuestionType(q_type),
                difficulty_range=difficulty_range,
                count=type_count,
                exclude_ids=[q.id for q in selected_questions]
            )
            
            selected_questions.extend(questions)
        
        # Shuffle for variety
        random.shuffle(selected_questions)
        
        return selected_questions[:count]

    async def get_review_priority_questions(
            self,
            user_id: UUID,
            facet_id: Optional[UUID] = None,
            count: int = 20
    ) -> List[Question]:
        """Get questions that should be prioritized for review."""
        # Get overdue cards first
        overdue_cards = await self.sr_repo.get_overdue_cards(user_id, facet_id, count)
        
        # Get due cards
        due_cards = await self.sr_repo.get_due_cards(user_id, facet_id, count - len(overdue_cards))
        
        # Combine and get questions
        all_cards = overdue_cards + due_cards
        question_ids = [card.question_id for card in all_cards]
        
        questions = []
        for question_id in question_ids:
            question = await self.question_repo.get_by_id(question_id)
            if question:
                questions.append(question)
        
        return questions

    async def get_recommended_facets(
            self,
            user_id: UUID,
            limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get recommended facets based on user's progress and learning patterns."""
        user_progress = await self.progress_repo.get_user_progress(user_id)
        
        if not user_progress or not user_progress.facet_progresses:
            # New user - recommend popular/beginner facets
            return await self._get_beginner_facets(limit)
        
        recommendations = []
        
        # Analyze user's learning patterns
        completed_facets = [
            fp for fp in user_progress.facet_progresses.values()
            if fp.is_complete()
        ]
        
        in_progress_facets = [
            fp for fp in user_progress.facet_progresses.values()
            if not fp.is_complete() and fp.seen_questions > 0
        ]
        
        # Recommend continuing in-progress facets
        for facet_progress in in_progress_facets:
            if len(recommendations) >= limit:
                break
                
            facet = await self.content_repo.get_facet(facet_progress.facet_id)
            if facet:
                recommendations.append({
                    'facet_id': facet.id,
                    'facet_name': facet.name,
                    'facet_code': facet.code,
                    'reason': 'continue_progress',
                    'progress_percentage': facet_progress.completion_percentage,
                    'mastery_score': facet_progress.mastery_score,
                    'priority': self._calculate_continuation_priority(facet_progress)
                })
        
        # Recommend related facets based on completed ones
        if len(recommendations) < limit:
            related_recommendations = await self._get_related_facets(
                completed_facets, limit - len(recommendations)
            )
            recommendations.extend(related_recommendations)
        
        # Sort by priority
        recommendations.sort(key=lambda x: x.get('priority', 0), reverse=True)
        
        return recommendations[:limit]

    async def _calculate_optimal_difficulty(
            self,
            user_id: UUID,
            facet_id: UUID,
            facet_progress: Optional[FacetProgress]
    ) -> tuple[int, int]:
        """Calculate optimal difficulty range for user."""
        if not facet_progress:
            # New facet - start with easy questions
            return (1, 3)
        
        # Base difficulty on current comfort level
        comfort = facet_progress.difficulty_comfort
        accuracy = facet_progress.accuracy_rate
        
        # Adjust based on performance
        if accuracy > 85:
            # Doing well, increase difficulty
            min_diff = max(1, int(comfort))
            max_diff = min(5, int(comfort) + 2)
        elif accuracy < 60:
            # Struggling, decrease difficulty
            min_diff = max(1, int(comfort) - 1)
            max_diff = max(3, int(comfort))
        else:
            # Balanced performance
            min_diff = max(1, int(comfort) - 1)
            max_diff = min(5, int(comfort) + 1)
        
        return (min_diff, max_diff)

    async def _calculate_question_distribution(
            self,
            user_id: UUID,
            facet_id: UUID,
            question_types: List[str],
            total_count: int
    ) -> Dict[str, int]:
        """Calculate optimal distribution of question types."""
        # Get facet to see available question types
        facet = await self.content_repo.get_facet(facet_id)
        available_types = facet.question_types if facet else question_types
        
        # Filter to only available types
        valid_types = [qt for qt in question_types if qt in available_types]
        
        if not valid_types:
            return {'mcq': total_count}
        
        # Get user's performance by question type (simplified)
        # In a real implementation, this would analyze historical performance
        
        # Default distribution
        if len(valid_types) == 1:
            return {valid_types[0]: total_count}
        
        distribution = {}
        base_count = total_count // len(valid_types)
        remainder = total_count % len(valid_types)
        
        for i, q_type in enumerate(valid_types):
            distribution[q_type] = base_count + (1 if i < remainder else 0)
        
        return distribution

    async def _get_questions_by_criteria(
            self,
            user_id: UUID,
            facet_id: UUID,
            question_type: QuestionType,
            difficulty_range: tuple[int, int],
            count: int,
            exclude_ids: List[UUID] = None
    ) -> List[Question]:
        """Get questions matching specific criteria."""
        exclude_ids = exclude_ids or []
        
        # Get unanswered questions first
        questions = await self.question_repo.get_unanswered_by_user(
            user_id=user_id,
            facet_id=facet_id,
            limit=count * 2  # Get more for filtering
        )
        
        # Filter by criteria
        filtered_questions = []
        for question in questions:
            if question.id in exclude_ids:
                continue
            if question.type != question_type:
                continue
            if not (difficulty_range[0] <= question.difficulty_level.value <= difficulty_range[1]):
                continue
            
            filtered_questions.append(question)
            
            if len(filtered_questions) >= count:
                break
        
        # If not enough unanswered questions, get some answered ones
        if len(filtered_questions) < count:
            additional_needed = count - len(filtered_questions)
            additional_questions = await self.question_repo.get_by_difficulty_range(
                facet_id=facet_id,
                min_difficulty=difficulty_range[0],
                max_difficulty=difficulty_range[1],
                limit=additional_needed * 2
            )
            
            for question in additional_questions:
                if question.id in exclude_ids:
                    continue
                if question.type != question_type:
                    continue
                if question in filtered_questions:
                    continue
                
                filtered_questions.append(question)
                
                if len(filtered_questions) >= count:
                    break
        
        return filtered_questions[:count]

    async def _get_beginner_facets(self, limit: int) -> List[Dict[str, Any]]:
        """Get recommended facets for beginners."""
        # Get topics and find beginner-friendly facets
        topics = await self.content_repo.get_all_topics()
        
        recommendations = []
        for topic in topics[:limit]:
            # Get first few facets from each topic
            subtopics = await self.content_repo.get_subtopics_by_topic(topic.id)
            
            for subtopic in subtopics[:2]:  # First 2 subtopics
                leaves = await self.content_repo.get_leaves_by_subtopic(subtopic.id)
                
                for leaf in leaves[:1]:  # First leaf
                    facets = await self.content_repo.get_facets_by_leaf(leaf.id)
                    
                    for facet in facets[:1]:  # First facet
                        recommendations.append({
                            'facet_id': facet.id,
                            'facet_name': facet.name,
                            'facet_code': facet.code,
                            'reason': 'beginner_friendly',
                            'progress_percentage': 0.0,
                            'mastery_score': 0.0,
                            'priority': random.randint(50, 100)
                        })
                        
                        if len(recommendations) >= limit:
                            return recommendations
        
        return recommendations

    async def _get_related_facets(
            self,
            completed_facets: List[FacetProgress],
            limit: int
    ) -> List[Dict[str, Any]]:
        """Get facets related to completed ones."""
        recommendations = []
        
        # Simple implementation: recommend facets from same topic/subtopic
        for facet_progress in completed_facets[:3]:  # Look at top 3 completed
            facet = await self.content_repo.get_facet(facet_progress.facet_id)
            if not facet:
                continue
            
            # Get other facets from same leaf
            related_facets = await self.content_repo.get_facets_by_leaf(facet.leaf_id)
            
            for related_facet in related_facets:
                if related_facet.id == facet.id:
                    continue
                    
                # Check if already completed
                if any(fp.facet_id == related_facet.id for fp in completed_facets):
                    continue
                
                recommendations.append({
                    'facet_id': related_facet.id,
                    'facet_name': related_facet.name,
                    'facet_code': related_facet.code,
                    'reason': f'related_to_{facet.code}',
                    'progress_percentage': 0.0,
                    'mastery_score': 0.0,
                    'priority': 70
                })
                
                if len(recommendations) >= limit:
                    break
        
        return recommendations[:limit]

    def _calculate_continuation_priority(self, facet_progress: FacetProgress) -> int:
        """Calculate priority for continuing a facet."""
        base_priority = 80
        
        # Higher priority for facets with more progress
        progress_bonus = facet_progress.completion_percentage * 0.3
        
        # Higher priority for recent activity
        recency_bonus = 20 if facet_progress.current_streak_days > 0 else 0
        
        # Lower priority if accuracy is very low (might need review of basics)
        accuracy_penalty = 0 if facet_progress.accuracy_rate > 40 else 10
        
        return int(base_priority + progress_bonus + recency_bonus - accuracy_penalty)