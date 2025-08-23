"""Django management command to import questions."""

import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from infrastructure.celery.tasks import import_question_file, import_questions_batch


class Command(BaseCommand):
    """Import questions from JSON files."""

    help = 'Import questions from JSON files'

    def add_arguments(self, parser):
        parser.add_argument(
            'paths',
            nargs='+',
            type=str,
            help='Paths to JSON files or directories'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Validate without importing'
        )
        parser.add_argument(
            '--async',
            action='store_true',
            help='Use Celery for async import'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Batch size for parallel import'
        )

    def handle(self, *args, **options):
        """Handle the command."""
        paths = options['paths']
        dry_run = options['dry_run']
        use_async = options['async']
        batch_size = options['batch_size']

        # Collect all JSON files
        json_files = []
        for path_str in paths:
            path = Path(path_str)

            if path.is_file() and path.suffix == '.json':
                json_files.append(str(path))
            elif path.is_dir():
                json_files.extend([str(f) for f in path.glob('*.json')])
            else:
                self.stdout.write(
                    self.style.WARNING(f'Skipping {path_str}: not a JSON file or directory')
                )

        if not json_files:
            raise CommandError('No JSON files found')

        self.stdout.write(f'Found {len(json_files)} JSON files to import')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No data will be saved'))
            self._validate_files(json_files)
        elif use_async:
            self._async_import(json_files, batch_size)
        else:
            self._sync_import(json_files)

    def _validate_files(self, files):
        """Validate files without importing."""
        from infrastructure.celery.tasks import validate_import_data

        total_valid = 0
        total_invalid = 0

        for file_path in files:
            result = validate_import_data(file_path)

            if 'error' in result:
                self.stdout.write(
                    self.style.ERROR(f"❌ {file_path}: {result['error']}")
                )
            else:
                total_valid += result['valid']
                total_invalid += result['invalid']

                if result['invalid'] > 0:
                    self.stdout.write(
                        self.style.WARNING(
                            f"⚠️  {file_path}: {result['valid']} valid, {result['invalid']} invalid"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f"✅ {file_path}: {result['valid']} valid")
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nValidation complete: {total_valid} valid, {total_invalid} invalid"
            )
        )

    def _async_import(self, files, batch_size):
        """Import files asynchronously using Celery."""
        # Split files into batches
        batches = [files[i:i + batch_size] for i in range(0, len(files), batch_size)]

        self.stdout.write(f'Queueing {len(batches)} batches for import...')

        for i, batch in enumerate(batches, 1):
            result = import_questions_batch.delay(batch)
            self.stdout.write(f'Batch {i} queued with task ID: {result.id}')

        self.stdout.write(
            self.style.SUCCESS('All batches queued. Check Celery logs for progress.')
        )

    def _sync_import(self, files):
        """Import files synchronously."""
        total_imported = 0
        total_skipped = 0
        total_errors = 0

        for file_path in files:
            self.stdout.write(f'Importing {file_path}...')

            try:
                result = import_question_file(file_path)
                total_imported += result['imported']
                total_skipped += result['skipped']
                total_errors += len(result['errors'])

                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✅ Imported: {result['imported']}, "
                        f"Skipped: {result['skipped']}, "
                        f"Errors: {len(result['errors'])}"
                    )
                )

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ❌ Failed: {e}"))
                total_errors += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\n🎉 Import complete!\n"
                f"  Total imported: {total_imported}\n"
                f"  Total skipped: {total_skipped}\n"
                f"  Total errors: {total_errors}"
            )
        )
