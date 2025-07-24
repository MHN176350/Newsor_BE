"""
Django management command to flush write-back cache operations to the database.
"""
from django.core.management.base import BaseCommand
from core.infrastructure.cache.base import WriteBackCache
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Flush write-back cache operations to the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--model',
            type=str,
            help='Specific model to flush (e.g., News, User, Comment)',
            default=None,
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show pending operations without executing them',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all pending operations without executing them',
        )

    def handle(self, *args, **options):
        model_name = options.get('model')
        dry_run = options.get('dry_run')
        clear = options.get('clear')

        write_back = WriteBackCache()

        if clear:
            self.stdout.write(f"Clearing pending operations for model: {model_name or 'all'}")
            write_back.clear_pending_operations(model_name)
            self.stdout.write(self.style.SUCCESS('Pending operations cleared'))
            return

        # Get pending operations
        pending_operations = write_back.get_pending_operations(model_name)
        
        if not pending_operations:
            self.stdout.write('No pending operations found')
            return

        self.stdout.write(f'Found {len(pending_operations)} pending operations')

        if dry_run:
            self.stdout.write('DRY RUN - Operations that would be executed:')
            for i, operation in enumerate(pending_operations, 1):
                self.stdout.write(
                    f"{i}. {operation['type'].upper()} {operation['model']} "
                    f"ID: {operation['id']} at {operation['timestamp']}"
                )
            return

        # Flush operations
        try:
            flushed_count = write_back.flush_operations(model_name)
            self.stdout.write(
                self.style.SUCCESS(f'Successfully flushed {flushed_count} operations to database')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error flushing operations: {e}')
            )
            logger.error(f'Error flushing write-back operations: {e}')
