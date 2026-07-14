from celery import Celery
from celery.schedules import crontab
from backend.app.core.config import settings

celery_app = Celery(
    "realestate_crm",  # app name
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.beat_schedule = {
    "check-stale-pipeline": {
        "task": "tasks.check_stale_pipeline",
        "schedule": crontab(hour=6, minute=0),
    }
}
celery_app.config.beat_schedule = {
    "check_stale_listing": {
        "task": "tasks.check_stale_listing",
        "schedule": crontab(hour=6, minutes=30),
    }
}
celery_app.conf.timezone = "UTC"
celery_app.autodiscover_tasks(["app.tasks"])
