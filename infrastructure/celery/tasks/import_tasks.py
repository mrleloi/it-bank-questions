"""Import-related Celery tasks."""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from celery import shared_task, group
from django.db import transaction

from infrastructure.persistence.models import QuestionModel, FacetModel
from infrastructure.importers import QuestionImporter

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def import_question_file(self, file_path: str) -> Dict[str, Any]:
    """Import questions from a single JSON file."""
    try:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Parse filename to get facet path
        # Format: backend_node_js__api__protocols__graphql.json
        filename = path.stem
        parts = filename.split('__')

        if len(parts) != 4:
            raise ValueError(f"Invalid filename format: {filename}")

        topic_code, subtopic_code, leaf_code, facet_code = parts

        # Get or create facet
        facet = FacetModel.objects.get_or_create_hierarchy(
            topic_code=topic_code,
            subtopic_code=subtopic_code,
            leaf_code=leaf_code,
            facet_code=facet_code
        )

        # Read and parse JSON
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

            imported = 0
            skipped = 0
            errors = []

            with transaction.atomic():
                for item in data:
                    try:
                        # Check if question already exists
                        if QuestionModel.objects.filter(external_id=item['id']).exists():
                            skipped += 1
                            continue

                        # Import question
                        importer = QuestionImporter()
                        question = importer.import_question(item, facet)
                        imported += 1

                    except Exception as e:
                        errors.append({
                            'question_id': item.get('id', 'unknown'),
                            'error': str(e)
                        })
                        logger.error(f"Failed to import question {item.get('id')}: {e}")

            # Update facet statistics
            facet.total_questions = facet.questions.count()
            facet.save()

            result = {
                'file': file_path,
                'facet': facet.get_full_path(),
                'imported': imported,
                'skipped': skipped,
                'errors': errors
            }

            logger.info(f"Import completed: {result}")
            return result

        except Exception as e:
        logger.error(f"Import failed for {file_path}: {e}")
        self.retry(countdown=60 * (self.request.retries + 1))

    @shared_task
    def import_questions_batch(file_paths: List[str]) -> Dict[str, Any]:
        """Import multiple question files in parallel."""
        # Create a group of import tasks
        job = group(import_question_file.s(path) for path in file_paths)
        result = job.apply_async()

        # Wait for all tasks to complete
        results = result.get(timeout=300)

        # Aggregate results
        total_imported = sum(r['imported'] for r in results)
        total_skipped = sum(r['skipped'] for r in results)
        total_errors = sum(len(r['errors']) for r in results)

        return {
            'total_files': len(file_paths),
            'total_imported': total_imported,
            'total_skipped': total_skipped,
            'total_errors': total_errors,
            'details': results
        }

    @shared_task
    def validate_import_data(file_path: str) -> Dict[str, Any]:
        """Validate import data without saving."""
        try:
            path = Path(file_path)

            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            valid = 0
            invalid = 0
            errors = []

            for item in data:
                try:
                    # Validate required fields
                    required = ['id', 'type', 'question']
                    for field in required:
                        if field not in item:
                            raise ValueError(f"Missing required field: {field}")

                    # Validate question type
                    if item['type'] not in ['mcq', 'theory', 'scenario']:
                        raise ValueError(f"Invalid question type: {item['type']}")

                    # Validate MCQ options
                    if item['type'] == 'mcq':
                        if 'options' not in item or 'answer' not in item:
                            raise ValueError("MCQ questions must have options and answer")

                        if item['answer'] not in item['options']:
                            raise ValueError("Answer must be one of the options")

                    valid += 1

                except Exception as e:
                    invalid += 1
                    errors.append({
                        'question_id': item.get('id', 'unknown'),
                        'error': str(e)
                    })

            return {
                'file': file_path,
                'total': len(data),
                'valid': valid,
                'invalid': invalid,
                'errors': errors[:10]  # Limit errors to first 10
            }

        except Exception as e:
            return {
                'file': file_path,
                'error': str(e)
            }


