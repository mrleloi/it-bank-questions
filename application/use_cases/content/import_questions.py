"""Import questions use case."""

import json
from pathlib import Path
from typing import Dict, Any, List
from uuid import UUID
from datetime import datetime

from domain.repositories import QuestionRepository, ContentRepository
from domain.services.content_hierarchy_service import ContentHierarchyService
from domain.value_objects import ContentPath
from application.dto.request import ImportQuestionsRequest
from application.dto.response import ImportResultResponse
from application.mappers import QuestionMapper


class ImportQuestionsUseCase:
    """Use case for importing questions from JSON files."""

    def __init__(
            self,
            question_repository: QuestionRepository,
            content_repository: ContentRepository,
            content_service: ContentHierarchyService
    ):
        self.question_repo = question_repository
        self.content_repo = content_repository
        self.content_service = content_service

    async def execute(self, request: ImportQuestionsRequest) -> ImportResultResponse:
        """Import questions from a JSON file."""
        # Validate request
        request.validate()

        start_time = datetime.now()

        # Parse file path
        file_path = Path(request.file_path)
        if not file_path.exists():
            raise ValueError(f"File not found: {request.file_path}")

        # Extract content path from filename
        # Format: backend_node_js__api__protocols__graphql.json
        filename = file_path.stem
        parts = filename.split('__')

        if len(parts) != 4:
            raise ValueError(f"Invalid filename format: {filename}")

        topic_code, subtopic_code, leaf_code, facet_code = parts

        # Ensure hierarchy exists
        facet = await self.content_repo.ensure_hierarchy(
            topic_code=topic_code,
            subtopic_code=subtopic_code,
            leaf_code=leaf_code,
            facet_code=facet_code
        )

        # Read JSON file
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        imported = 0
        skipped = 0
        failed = 0
        errors = []

        # Process each question
        for item in data:
            try:
                # Check if question already exists
                existing = await self.question_repo.get_by_external_id(item['id'])
                if existing:
                    skipped += 1
                    continue

                # Create question entity
                question = QuestionMapper.from_import_data(item, facet.id)

                # Validate
                question.validate()

                # Save if not dry run
                if not request.dry_run:
                    await self.question_repo.save(question)

                imported += 1

            except Exception as e:
                failed += 1
                errors.append({
                    'question_id': item.get('id', 'unknown'),
                    'error': str(e)
                })

        # Update facet statistics
        if not request.dry_run:
            facet.total_questions = await self.question_repo.count(
                facet_id=facet.id
            )
            await self.content_repo.save(facet)

        processing_time = (datetime.now() - start_time).total_seconds()

        return ImportResultResponse(
            imported=imported,
            skipped=skipped,
            failed=failed,
            errors=errors,
            processing_time_seconds=processing_time
        )