import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from django.core.management.base import BaseCommand
from django.db import transaction, connection
from django.db.utils import IntegrityError

from infrastructure.persistence.models import (
    TopicModel, SubtopicModel, LeafModel, FacetModel, QuestionModel, MCQOptionModel
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Optimized import command with parallel processing."""

    help = 'Import questions from JSON files with optimized parallel processing'

    def add_arguments(self, parser):
        parser.add_argument(
            'directory',
            type=str,
            help='Directory containing JSON files'
        )
        parser.add_argument(
            '--workers',
            type=int,
            default=4,
            help='Number of parallel workers (default: 4)'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Questions per batch for bulk insert (default: 100)'
        )
        parser.add_argument(
            '--pre-create-hierarchy',
            action='store_true',
            help='Pre-create all hierarchy nodes before import'
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            default=True,
            help='Skip existing questions (default: True)'
        )

    def handle(self, *args, **options):
        directory = Path(options['directory'])
        workers = options['workers']
        batch_size = options['batch_size']
        pre_create = options['pre_create_hierarchy']
        skip_existing = options['skip_existing']

        # Find all JSON files
        json_files = list(directory.glob('*.json'))
        self.stdout.write(f"Found {len(json_files)} JSON files")

        # Step 1: Pre-create hierarchy if requested (RECOMMENDED)
        if pre_create:
            self.stdout.write("Pre-creating content hierarchy...")
            self.pre_create_hierarchy(json_files)

        # Step 2: Import questions in parallel
        self.stdout.write(f"Starting parallel import with {workers} workers...")
        results = self.parallel_import(
            json_files,
            workers=workers,
            batch_size=batch_size,
            skip_existing=skip_existing
        )

        # Step 3: Report results
        self.report_results(results)

    def pre_create_hierarchy(self, json_files: List[Path]):
        """Pre-create all hierarchy nodes to avoid race conditions."""
        hierarchy_map = {}

        # Extract unique hierarchy paths from filenames
        for file_path in json_files:
            parts = file_path.stem.split('__')
            if len(parts) >= 4:
                topic_code = parts[0]
                subtopic_code = parts[1]
                leaf_code = parts[2]
                facet_code = parts[3]

                # Store unique paths
                if topic_code not in hierarchy_map:
                    hierarchy_map[topic_code] = {}
                if subtopic_code not in hierarchy_map[topic_code]:
                    hierarchy_map[topic_code][subtopic_code] = {}
                if leaf_code not in hierarchy_map[topic_code][subtopic_code]:
                    hierarchy_map[topic_code][subtopic_code][leaf_code] = set()
                hierarchy_map[topic_code][subtopic_code][leaf_code].add(facet_code)

        # Create hierarchy in order: Topics → Subtopics → Leaves → Facets
        with transaction.atomic():
            # Create topics
            for topic_code in hierarchy_map:
                TopicModel.objects.get_or_create(
                    code=topic_code,
                    defaults={'name': topic_code.replace('_', ' ').title()}
                )

            # Create subtopics
            for topic_code, subtopics in hierarchy_map.items():
                topic = TopicModel.objects.get(code=topic_code)
                for subtopic_code in subtopics:
                    SubtopicModel.objects.get_or_create(
                        topic=topic,
                        code=subtopic_code,
                        defaults={'name': subtopic_code.replace('_', ' ').title()}
                    )

            # Create leaves
            for topic_code, subtopics in hierarchy_map.items():
                topic = TopicModel.objects.get(code=topic_code)
                for subtopic_code, leaves in subtopics.items():
                    subtopic = SubtopicModel.objects.get(topic=topic, code=subtopic_code)
                    for leaf_code in leaves:
                        LeafModel.objects.get_or_create(
                            subtopic=subtopic,
                            code=leaf_code,
                            defaults={'name': leaf_code.replace('_', ' ').title()}
                        )

            # Create facets
            for topic_code, subtopics in hierarchy_map.items():
                topic = TopicModel.objects.get(code=topic_code)
                for subtopic_code, leaves in subtopics.items():
                    subtopic = SubtopicModel.objects.get(topic=topic, code=subtopic_code)
                    for leaf_code, facets in leaves.items():
                        leaf = LeafModel.objects.get(subtopic=subtopic, code=leaf_code)
                        for facet_code in facets:
                            FacetModel.objects.get_or_create(
                                leaf=leaf,
                                code=facet_code,
                                defaults={'name': facet_code.replace('_', ' ').title()}
                            )

        self.stdout.write(self.style.SUCCESS("✓ Hierarchy pre-created successfully"))

    def parallel_import(
        self,
        json_files: List[Path],
        workers: int,
        batch_size: int,
        skip_existing: bool
    ) -> Dict[str, Any]:
        """Import files in parallel using thread pool."""

        total_imported = 0
        total_skipped = 0
        total_errors = 0
        file_results = []

        # Create a thread pool
        with ThreadPoolExecutor(max_workers=workers) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(
                    self.import_single_file,
                    file_path,
                    batch_size,
                    skip_existing
                ): file_path
                for file_path in json_files
            }

            # Process completed tasks
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    result = future.result()
                    file_results.append(result)
                    total_imported += result['imported']
                    total_skipped += result['skipped']
                    total_errors += len(result['errors'])

                    # Progress update
                    completed = len(file_results)
                    self.stdout.write(
                        f"Progress: {completed}/{len(json_files)} files "
                        f"({total_imported} imported, {total_skipped} skipped)"
                    )

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Failed to process {file_path}: {e}")
                    )
                    total_errors += 1

        return {
            'total_files': len(json_files),
            'total_imported': total_imported,
            'total_skipped': total_skipped,
            'total_errors': total_errors,
            'file_results': file_results
        }

    def import_single_file(
        self,
        file_path: Path,
        batch_size: int,
        skip_existing: bool
    ) -> Dict[str, Any]:
        """Import a single JSON file."""

        # Parse hierarchy from filename
        parts = file_path.stem.split('__')
        if len(parts) < 4:
            return {
                'file': str(file_path),
                'imported': 0,
                'skipped': 0,
                'errors': [f"Invalid filename format: {file_path.stem}"]
            }

        topic_code, subtopic_code, leaf_code, facet_code_raw = parts[0], parts[1], parts[2], parts[3]

        # Extract facet code (remove question type suffix)
        facet_code = facet_code_raw
        for suffix in ['_mcq', '_theory', '_scenario']:
            if suffix in facet_code_raw:
                facet_code = facet_code_raw.split(suffix)[0]
                break

        try:
            # Get facet (should already exist if pre-created)
            facet = FacetModel.objects.select_related('leaf__subtopic__topic').get(
                leaf__subtopic__topic__code=topic_code,
                leaf__subtopic__code=subtopic_code,
                leaf__code=leaf_code,
                code=facet_code
            )
        except FacetModel.DoesNotExist:
            # Fallback: create hierarchy if not pre-created
            facet = FacetModel.objects.get_or_create_hierarchy(
                topic_code=topic_code,
                subtopic_code=subtopic_code,
                leaf_code=leaf_code,
                facet_code=facet_code
            )

        # Load JSON data
        with open(file_path, 'r', encoding='utf-8') as f:
            questions_data = json.load(f)

        imported = 0
        skipped = 0
        errors = []

        # Process in batches for bulk operations
        for i in range(0, len(questions_data), batch_size):
            batch = questions_data[i:i + batch_size]

            try:
                batch_results = self.import_batch(
                    batch,
                    facet,
                    skip_existing
                )
                imported += batch_results['imported']
                skipped += batch_results['skipped']
                errors.extend(batch_results['errors'])

            except Exception as e:
                errors.append(f"Batch {i//batch_size + 1} error: {str(e)}")

        # Update facet statistics
        facet.total_questions = facet.questions.count()
        facet.save(update_fields=['total_questions'])

        return {
            'file': str(file_path),
            'facet': facet.get_full_path(),
            'imported': imported,
            'skipped': skipped,
            'errors': errors[:10]  # Limit errors in response
        }

    def import_batch(
        self,
        batch: List[Dict],
        facet: FacetModel,
        skip_existing: bool
    ) -> Dict[str, Any]:
        """Import a batch of questions efficiently."""

        imported = 0
        skipped = 0
        errors = []

        # Filter out existing questions if skip_existing
        if skip_existing:
            external_ids = [q['id'] for q in batch]
            existing_ids = set(
                QuestionModel.objects.filter(
                    external_id__in=external_ids
                ).values_list('external_id', flat=True)
            )

            new_questions = [q for q in batch if q['id'] not in existing_ids]
            skipped = len(batch) - len(new_questions)
        else:
            new_questions = batch

        if not new_questions:
            return {'imported': 0, 'skipped': skipped, 'errors': []}

        # Prepare question models for bulk create
        question_models = []
        mcq_options_data = []  # Store for later bulk create

        for q_data in new_questions:
            try:
                # Create question model
                question = QuestionModel(
                    external_id=q_data['id'],
                    facet=facet,
                    type=q_data['type'],
                    question=q_data['question'],
                    difficulty_level=q_data.get('difficulty', 2),
                    source='hard_resource',
                    tags=q_data.get('tags', []),
                    hints=q_data.get('hints', []),
                    references=q_data.get('references', []),
                    sample_answer=q_data.get('sample_answer', ''),
                    evaluation_criteria=q_data.get('evaluation_criteria', ''),
                    estimated_time_seconds=q_data.get('estimated_time_seconds', 60)
                )
                question_models.append(question)

                # Store MCQ options for later
                if q_data['type'] == 'mcq' and 'options' in q_data:
                    mcq_options_data.append({
                        'external_id': q_data['id'],
                        'options': q_data['options'],
                        'answer': q_data.get('answer')
                    })

            except Exception as e:
                errors.append(f"Question {q_data.get('id')}: {str(e)}")

        # Bulk create questions
        if question_models:
            try:
                created_questions = QuestionModel.objects.bulk_create(
                    question_models,
                    ignore_conflicts=True
                )
                imported = len(created_questions)

                # Create MCQ options
                if mcq_options_data:
                    self.create_mcq_options(created_questions, mcq_options_data)

            except IntegrityError as e:
                errors.append(f"Database integrity error: {str(e)}")

        return {
            'imported': imported,
            'skipped': skipped,
            'errors': errors
        }

    def create_mcq_options(
        self,
        questions: List[QuestionModel],
        options_data: List[Dict]
    ):
        """Bulk create MCQ options."""

        # Map questions by external_id for quick lookup
        question_map = {q.external_id: q for q in questions}

        option_models = []
        for data in options_data:
            question = question_map.get(data['external_id'])
            if not question:
                continue

            correct_answer = data.get('answer')
            for key, text in data['options'].items():
                option = MCQOptionModel(
                    question=question,
                    option_key=key,
                    option_text=text,
                    is_correct=(key == correct_answer),
                    explanation=""
                )
                option_models.append(option)

        if option_models:
            MCQOptionModel.objects.bulk_create(option_models, ignore_conflicts=True)

    def report_results(self, results: Dict[str, Any]):
        """Report import results."""

        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS("IMPORT COMPLETED"))
        self.stdout.write("="*50)

        self.stdout.write(f"Total Files: {results['total_files']}")
        self.stdout.write(f"Total Imported: {results['total_imported']:,}")
        self.stdout.write(f"Total Skipped: {results['total_skipped']:,}")
        self.stdout.write(f"Total Errors: {results['total_errors']}")

        # Show files with errors
        files_with_errors = [
            r for r in results['file_results']
            if r.get('errors')
        ]

        if files_with_errors:
            self.stdout.write("\nFiles with errors:")
            for file_result in files_with_errors[:10]:  # Show first 10
                self.stdout.write(f"  - {file_result['file']}: {len(file_result['errors'])} errors")