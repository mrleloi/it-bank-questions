"""Search content use case."""

from typing import List

from domain.repositories import ContentRepository
from domain.value_objects import ContentLevel
from application.dto.request import SearchContentRequest
from application.dto.response import ContentNodeResponse
from application.mappers import ContentMapper


class SearchContentUseCase:
    """Use case for searching content across hierarchy."""

    def __init__(self, content_repository: ContentRepository):
        self.content_repo = content_repository

    async def execute(self, request: SearchContentRequest) -> List[ContentNodeResponse]:
        """Search content and return results."""
        # Validate request
        request.validate()

        # Convert level string to enum if provided
        level = None
        if request.level:
            try:
                level = ContentLevel(request.level)
            except ValueError:
                raise ValueError(f"Invalid content level: {request.level}")

        # Search content
        search_results = await self.content_repo.search_content(
            query=request.query,
            level=level,
            limit=request.limit
        )

        # Convert results to response DTOs
        responses = []
        for result in search_results:
            # Create appropriate response based on level
            node_response = ContentNodeResponse(
                id=result['id'],
                code=result['code'],
                name=result['name'],
                description=result.get('description'),
                level=result['level'],
                parent_id=result.get('parent_id'),
                total_questions=result.get('total_questions', 0),
                total_learners=result.get('total_learners', 0),
                average_mastery=result.get('average_mastery', 0.0)
            )
            
            # Add facet-specific fields if applicable
            if result['level'] == 'facet':
                node_response.question_types = result.get('question_types', [])
                node_response.difficulty_distribution = result.get('difficulty_distribution', {})

            responses.append(node_response)

        return responses

    async def search_with_filters(
            self,
            query: str,
            filters: dict,
            limit: int = 20
    ) -> List[ContentNodeResponse]:
        """Advanced search with additional filters."""
        # This could be extended for more complex search scenarios
        
        # Basic filters
        level = filters.get('level')
        min_questions = filters.get('min_questions', 0)
        min_mastery = filters.get('min_mastery', 0.0)
        question_types = filters.get('question_types', [])
        
        # Search content
        search_results = await self.content_repo.search_content(
            query=query,
            level=ContentLevel(level) if level else None,
            limit=limit * 2  # Get more results for filtering
        )
        
        # Apply additional filters
        filtered_results = []
        for result in search_results:
            # Filter by minimum questions
            if result.get('total_questions', 0) < min_questions:
                continue
                
            # Filter by minimum mastery
            if result.get('average_mastery', 0.0) < min_mastery:
                continue
                
            # Filter by question types (for facets)
            if question_types and result['level'] == 'facet':
                facet_types = result.get('question_types', [])
                if not any(qt in facet_types for qt in question_types):
                    continue
            
            filtered_results.append(result)
            
            # Stop if we have enough results
            if len(filtered_results) >= limit:
                break
        
        # Convert to response DTOs
        responses = []
        for result in filtered_results:
            node_response = ContentNodeResponse(
                id=result['id'],
                code=result['code'],
                name=result['name'],
                description=result.get('description'),
                level=result['level'],
                parent_id=result.get('parent_id'),
                total_questions=result.get('total_questions', 0),
                total_learners=result.get('total_learners', 0),
                average_mastery=result.get('average_mastery', 0.0)
            )
            
            if result['level'] == 'facet':
                node_response.question_types = result.get('question_types', [])
                node_response.difficulty_distribution = result.get('difficulty_distribution', {})
                
            responses.append(node_response)
        
        return responses

    async def get_search_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """Get search suggestions based on query."""
        # This would typically use a dedicated search index or database
        # For now, we'll do a simple content search and extract names
        
        if len(query) < 2:
            return []
            
        search_results = await self.content_repo.search_content(
            query=query,
            limit=limit
        )
        
        # Extract unique names/codes as suggestions
        suggestions = set()
        for result in search_results:
            suggestions.add(result['name'])
            suggestions.add(result['code'])
            
            # Add partial matches
            name_lower = result['name'].lower()
            code_lower = result['code'].lower()
            query_lower = query.lower()
            
            # Add name if it contains the query
            if query_lower in name_lower:
                suggestions.add(result['name'])
                
            # Add code if it contains the query  
            if query_lower in code_lower:
                suggestions.add(result['code'])
        
        # Return sorted suggestions
        return sorted(list(suggestions))[:limit]