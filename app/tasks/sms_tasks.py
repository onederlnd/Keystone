# app/tasks/sms_tasks.py

from app.core.celery_app import celery_app


@celery_app.task(name="tasks.send_listing_status_sms")
def send_listing_status_sms(listing_id):
    pass


@celery_app.task(name="tasks.send_document_ready_sms")
def send_document_ready_sms(document_id):
    pass


@celery_app.task(name="tasks.send_pipeline_stage_sms")
def send_pipeline_stage_sms(pipeline_id):
    pass
