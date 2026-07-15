# app/tasks/celery_app.py

import asyncio
import functools

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "keystone",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
)

celery_app.autodiscover_tasks(["backend.app.tasks"], related_name="email_tasks")
celery_app.autodiscover_tasks(["backend.app.tasks"], related_name="sms_tasks")

celery_app.conf.task_track_started = True


def async_task(*args, **kwargs):
    def decorator(func):
        @celery_app.task(*args, **kwargs)
        @functools.wraps(func)
        def wrapper(*f_args, **f_kwargs):
            return asyncio.run(func(*f_args, **f_kwargs))

        return wrapper

    return decorator
