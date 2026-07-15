# app/tasks/pipeline_tasks.py

from app.core.celery_app import celery_app


@celery_app.task(name="tasks.check_stale_pipeline")
def check_stale_pipeline():
    """Periodic task: finds pipeline enteries that haven't changed stages in
    a while and (eventually) flag/notify on them."""
    pass
