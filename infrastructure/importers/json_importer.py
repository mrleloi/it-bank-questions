"""JSON question importer."""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from uuid import UUID

from domain.entities import Question, MCQOption, QuestionMetadata
from domain.value_objects import QuestionType, QuestionSource, DifficultyLevel
from domain.repositories import QuestionRepository, ContentRepository
from .base_importer import BaseImporter, ImportContext, ImportResult

logger = logging.getLogger(__name__)


class JsonQuestionImporter(BaseImporter):
    """Importer for JSON question files."""

    def __init__(
        self,
        question_repository: QuestionRepository,
        content_repository: ContentRepository,
        batch_size: int = 50
    ):
        super().__init__(batch_size)
        self.question_repo = question_repository
        self.content_repo = content_repository

    def validate_file(self, file_path: Path) -> bool:
        """Validate if file can be imported."""
        try:
            # Check file extension
            if file_path.suffix.lower() != '.json':
                return False

            # Check file exists and is readable
            if not file_path.exists() or not file_path.is_file():
                return False

            # Try to parse JSON
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Must be a list
            if not isinstance(data, list):
                return False

            # Must have at least one item
            if len(data) == 0:
                return False

            # Check first item has required fields
            first_item = data[0]
            required_fields = ['id', 'type', 'question']
            
            for field in required_fields:
                if field not in first_item:
                    return False

            return True

        except Exception as e:
            logger.error(f"File validation failed: {e}")
            return False

    def parse_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse JSON file and return list of question items."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if not isinstance(data, list):
                raise ValueError("JSON file must contain an array of questions")

            logger.info(f"Parsed {len(data)} questions from {file_path}")
            return data

        except Exception as e:
            logger.error(f"Failed to parse file {file_path}: {e}")
            raise

    def validate_item(self, item: Dict[str, Any]) -> List[str]:
        """Validate single question item."""
        errors = []

        # Required fields
        required_fields = ['id', 'type', 'question']
        for field in required_fields:
            if field not in item:
                errors.append(f"Missing required field: {field}")
            elif not item[field] or not str(item[field]).strip():
                errors.append(f"Empty required field: {field}")

        # Validate question type
        if 'type' in item:
            valid_types = ['mcq', 'theory', 'scenario']
            if item['type'] not in valid_types:
                errors.append(f"Invalid question type: {item['type']}. Must be one of: {valid_types}")

        # MCQ specific validation
        if item.get('type') == 'mcq':
            if 'options' not in item:
                errors.append("MCQ questions must have 'options' field")
            elif not isinstance(item['options'], dict):
                errors.append("MCQ 'options' must be a dictionary")
            elif len(item['options']) < 2:
                errors.append("MCQ must have at least 2 options")
            else:
                # Validate answer exists in options
                if 'answer' not in item:
                    errors.append("MCQ questions must have 'answer' field")
                elif item['answer'] not in item['options']:
                    errors.append(f"Answer '{item['answer']}' not found in options")

                # Validate option keys
                valid_keys = ['A', 'B', 'C', 'D', 'E', 'F']
                for key in item['options'].keys():
                    if key not in valid_keys:
                        errors.append(f"Invalid option key: {key}. Must be one of: {valid_keys}")

        # Validate ID format
        if 'id' in item:
            expected_parts = 5  # topic__subtopic__leaf__facet_type_number
            parts = item['id'].split('__')
            if len(parts) < 4:
                errors.append(f"Invalid ID format: {item['id']}. Expected format: topic__subtopic__leaf__facet_type_number")

        return errors

    async def item_exists(self, item: Dict[str, Any]) -> bool:
        """Check if question already exists."""
        try:
            existing = await self.question_repo.get_by_external_id(item['id'])
            return existing is not None
        except Exception as e:
            logger.error(f"Error checking if item exists: {e}")
            return False

    async def import_item(self, item: Dict[str, Any], context: ImportContext) -> bool:
        """Import single question item."""
        try:
            # Parse facet from question ID
            facet = await self._ensure_facet_exists(item['id'])
            if not facet:
                logger.error(f"Could not create/find facet for question: {item['id']}")
                return False

            # Create question entity
            question = await self._create_question_entity(item, facet.id, context)

            # Save question
            await self.question_repo.save(question)
            
            # Update facet statistics
            # facet.update_statistics(question.type.value, question.difficulty_level.value)
            # await self.content_repo.save(facet)

            logger.debug(f"Successfully imported question: {item['id']}")
            return True

        except Exception as e:
            logger.error(f"Failed to import question {item['id']}: {e}", exc_info=True)
            return False

    async def _ensure_facet_exists(self, question_id: str):
        """Ensure facet exists for question, create hierarchy if needed."""
        try:
            # Parse question ID: topic__subtopic__leaf__facet_type_number
            parts = question_id.split('__')
            if len(parts) < 4:
                raise ValueError(f"Invalid question ID format: {question_id}")

            # Extract last part and split by type
            topic_code, subtopic_code, leaf_code = parts[0], parts[1], parts[2]
            
            # Parse facet from remaining parts and question type
            facet_part = parts[3]  # e.g., "graphql_mcq_000001"
            
            # Find question type suffix
            type_suffixes = ['_mcq_', '_theory_', '_scenario_']
            facet_code = facet_part
            
            for suffix in type_suffixes:
                if suffix in facet_part:
                    facet_code = facet_part.split(suffix)[0]
                    break

            # Ensure complete hierarchy exists
            facet = await self.content_repo.ensure_hierarchy(
                topic_code=topic_code,
                subtopic_code=subtopic_code, 
                leaf_code=leaf_code,
                facet_code=facet_code
            )

            return facet

        except Exception as e:
            logger.error(f"Failed to ensure facet exists for {question_id}: {e}", exc_info=True)
            return None

    async def _create_question_entity(
            self, 
            item: Dict[str, Any], 
            facet_id: UUID,
            context: ImportContext
    ) -> Question:
        """Create question entity from item data."""
        # Basic question data
        question_type = QuestionType(item['type'])
        question_text = item['question']
        
        # Determine difficulty level
        difficulty = DifficultyLevel.MEDIUM  # Default
        if 'difficulty' in item:
            try:
                difficulty = DifficultyLevel(int(item['difficulty']))
            except (ValueError, TypeError):
                pass

        # Create metadata
        metadata = QuestionMetadata(
            tags=item.get('tags', []),
            hints=item.get('hints', []),
            references=item.get('references', []),
            learning_objectives=item.get('learning_objectives', []),
            prerequisites=item.get('prerequisites', []),
            estimated_time_seconds=item.get('estimated_time_seconds'),
        )

        # Create MCQ options if applicable
        options = []
        if question_type == QuestionType.MCQ and 'options' in item:
            correct_answer = item.get('answer')
            explanation = item.get('explanation')
            
            for key, text in item['options'].items():
                option = MCQOption(
                    key=key,
                    text=text,
                    is_correct=(key == correct_answer),
                    explanation=explanation if key == correct_answer else None
                )
                options.append(option)

        # Determine source
        source = QuestionSource.HARD_RESOURCE
        if context.source:
            try:
                source = QuestionSource(context.source)
            except ValueError:
                pass

        # Create question entity
        question = Question(
            external_id=item['id'],
            facet_id=facet_id,
            type=question_type,
            question_text=question_text,
            difficulty_level=difficulty,
            source=source,
            metadata=metadata,
            options=options,
            sample_answer=item.get('sample_answer'),
            evaluation_criteria=item.get('evaluation_criteria'),
            is_active=True
        )

        return question

    def get_supported_extensions(self) -> List[str]:
        """Get supported file extensions."""
        return ['.json']

    def extract_facet_info_from_filename(self, file_path: Path) -> Optional[Dict[str, str]]:
        """Extract facet information from filename."""
        try:
            # Expected format: topic__subtopic__leaf__facet.json
            filename = file_path.stem
            parts = filename.split('__')
            
            if len(parts) == 4:
                return {
                    'topic': parts[0],
                    'subtopic': parts[1], 
                    'leaf': parts[2],
                    'facet': parts[3]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to extract facet info from filename {file_path}: {e}")
            return None

    async def bulk_import_directory(
            self, 
            directory_path: Path,
            file_pattern: str = "*.json",
            dry_run: bool = False,
            parallel: bool = True
    ) -> List[Dict[str, Any]]:
        """Import all JSON files from directory."""
        results = []
        
        try:
            json_files = list(directory_path.glob(file_pattern))
            logger.info(f"Found {len(json_files)} JSON files in {directory_path}")
            
            if parallel and len(json_files) > 1:
                # Process files in parallel
                import asyncio
                
                async def import_file_task(file_path):
                    context = ImportContext(
                        file_path=file_path,
                        dry_run=dry_run,
                        batch_size=self.batch_size,
                        source="hard_resource"
                    )
                    return await self.import_file(context)
                
                # Create tasks for all files
                tasks = [import_file_task(file_path) for file_path in json_files]
                
                # Execute with limited concurrency
                semaphore = asyncio.Semaphore(5)  # Max 5 concurrent imports
                
                async def bounded_import(task):
                    async with semaphore:
                        return await task
                
                bounded_tasks = [bounded_import(task) for task in tasks]
                results = await asyncio.gather(*bounded_tasks, return_exceptions=True)
                
                # Convert exceptions to error results
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        results[i] = ImportResult(
                            file_path=str(json_files[i]),
                            total_items=0,
                            imported=0,
                            failed=1
                        )
                        results[i].add_error('import', str(result))
            else:
                # Process files sequentially
                for file_path in json_files:
                    context = ImportContext(
                        file_path=file_path,
                        dry_run=dry_run,
                        batch_size=self.batch_size,
                        source="hard_resource"
                    )
                    result = await self.import_file(context)
                    results.append(result)
            
            # Calculate summary statistics
            total_files = len(results)
            total_imported = sum(r.imported for r in results if hasattr(r, 'imported'))
            total_failed = sum(r.failed for r in results if hasattr(r, 'failed'))
            
            logger.info(
                f"Bulk import completed: {total_files} files processed, "
                f"{total_imported} questions imported, {total_failed} failed"
            )
            
            return [r.to_dict() if hasattr(r, 'to_dict') else r for r in results]
            
        except Exception as e:
            logger.error(f"Bulk import failed: {e}", exc_info=True)
            raise