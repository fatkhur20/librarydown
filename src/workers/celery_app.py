from celery import Celery
from celery.schedules import crontab
from src.core.config import settings

celery_app = Celery(
    "librarydown",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["src.workers.tasks", "src.workers.cleanup"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    
    # Scheduled tasks
    beat_schedule={
        'cleanup-old-files': {
            'task': 'src.workers.cleanup.cleanup_old_files',
            'schedule': crontab(hour='*/1', minute=0),  # Run every hour
        },
    },
)
