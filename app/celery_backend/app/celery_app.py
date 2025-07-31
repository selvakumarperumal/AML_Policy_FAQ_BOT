from celery import Celery

celery_app = Celery(
    'celery_backend',
    broker='redis://redis:6379/0',
)
celery_app.conf.timezone = 'UTC'

celery_app.conf.beat_schedule = {
    'cleanup-expired-sessions': {
        'task': 'cleanup_expired_sessions',  # Short name!
        'schedule': 10,
    },
}

# Register tasks by importing the tasks module
import app.celery_backend.app.tasks