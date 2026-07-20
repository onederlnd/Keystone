# app/core/celery_app.py

import asyncio
from functools import wraps
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings


def async_task(func):
    @wraps(func)
    def wrapper(*a, **kw):
        return asyncio.run(func(*a, **kw))

    return wrapper


celery_app = Celery(
    "realestate_crm",  # app name
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.beat_schedule = {
    "check_stale_pipeline": {
        "task": "tasks.check_stale_pipeline",
        "schedule": crontab(hour=4, minute=0),  # 04:00
    },
    "check_stale_listing": {
        "task": "tasks.check_stale_listing",
        "schedule": crontab(hour=4, minute=30),  # 04:30
    },
}

celery_app.conf.timezone = "UTC"
celery_app.autodiscover_tasks(["app.tasks"])
