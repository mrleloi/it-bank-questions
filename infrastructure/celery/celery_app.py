"""Celery application configuration."""

import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Create Celery app
app = Celery('learning_platform')

# Configure Celery
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load tasks from all registered Django apps
app.autodiscover_tasks()

# Celery beat schedule
app.conf.beat_schedule = {
    'cleanup-expired-sessions': {
        'task': 'infrastructure.celery.tasks.cleanup_tasks.cleanup_expired_sessions',
        'schedule': crontab(minute=0, hour='*/4'),  # Every 4 hours
    },
    'calculate-daily-statistics': {
        'task': 'infrastructure.celery.tasks.analytics_tasks.calculate_daily_statistics',
        'schedule': crontab(minute=0, hour=2),  # Daily at 2 AM
    },
    'send-daily-reminders': {
        'task': 'infrastructure.celery.tasks.notification_tasks.send_daily_reminders',
        'schedule': crontab(minute=0, hour=9),  # Daily at 9 AM
    },
    'update-user-streaks': {
        'task': 'infrastructure.celery.tasks.progress_tasks.update_user_streaks',
        'schedule': crontab(minute=0, hour=0),  # Daily at midnight
    },
    'generate-review-cards': {
        'task': 'infrastructure.celery.tasks.learning_tasks.generate_daily_review_cards',
        'schedule': crontab(minute=0, hour=6),  # Daily at 6 AM
    },
    'backup-database': {
        'task': 'infrastructure.celery.tasks.maintenance_tasks.backup_database',
        'schedule': crontab(minute=0, hour=3, day_of_week=0),  # Weekly on Sunday at 3 AM
    },
}

# Celery configuration
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)