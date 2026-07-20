# app/tasks/email_tasks.py

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from celery import shared_task
from app.core.celery_app import async_task
from app.core.database import AsyncSessionLocal
from app.core.notifications import send_email
from app.tasks.base import NotificationTask
from app.models.listing import Listings
from app.models.document import Documents
from app.models.pipeline import Pipelines
from app.models.contact import Contacts

LISTING_ROLES = {"agent", "seller"}
PIPELINE_ROLES = {"agent", "contact"}


def _resolve_recipient(entity, recipient_role, allowed_roles):
    if recipient_role not in allowed_roles:
        return None
    return getattr(entity, recipient_role, None)


@shared_task(
    name="tasks.send_listing_status_email",
    base=NotificationTask,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
@async_task
async def send_listing_status_email(listing_id, recipient_role, entity_type):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Listings)
            .options(selectinload(Listings.agent), selectinload(Listings.seller))
            .where(Listings.id == listing_id)
        )
        listing = result.scalar_one_or_none()
        if not listing:
            return

        recipient = _resolve_recipient(listing, recipient_role, LISTING_ROLES)
        if not recipient:
            return

        context = {
            "template": "listing_status",
            "address": listing.address,
            "status": listing.status,
            "price": listing.price,
        }

        await send_email(
            to=recipient.email,
            subject=f"Listing updated: {listing.address}",
            body=context,
        )


@shared_task(
    name="tasks.send_document_ready_email",
    base=NotificationTask,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
@async_task
async def send_document_ready_email(document_id, entity_type):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Documents)
            .options(selectinload(Documents.contact))
            .where(Documents.id == document_id)
        )
        document = result.scalar_one_or_none()
        if not document:
            return

        recipient = document.contact
        if not recipient:
            return

        context = {
            "template": "document_ready",
            "type": document.type,
            "status": document.status,
        }

        await send_email(
            to=recipient.email,
            subject=f"Document ready: {document.type}",
            body=context,
        )


@shared_task(
    name="tasks.send_pipeline_stage_email",
    base=NotificationTask,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
@async_task
async def send_pipeline_stage_email(pipeline_id, recipient_role, entity_type):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Pipelines)
            .options(selectinload(Pipelines.agent), selectinload(Pipelines.contact))
            .where(Pipelines.id == pipeline_id)
        )
        pipeline = result.scalar_one_or_none()
        if not pipeline:
            return

        recipient = _resolve_recipient(pipeline, recipient_role, PIPELINE_ROLES)
        if not recipient:
            return

        context = {
            "template": "pipeline_stage",
            "stage": pipeline.stage,
            "offer_price": pipeline.offer_price,
        }

        await send_email(
            to=recipient.email,
            subject=f"Pipeline update: {pipeline.stage}",
            body=context,
        )


@shared_task(
    name="tasks.send_new_contact_email",
    base=NotificationTask,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
@async_task
async def send_new_contact_email(contact_id, entity_type):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Contacts)
            .options(selectinload(Contacts.agent))
            .where(Contacts.id == contact_id)
        )
        contact = result.scalar_one_or_none()
        if not contact:
            return

        agent = contact.agent
        if not agent:
            return

        context = {
            "template": "new_contact",
            "full_name": contact.full_name,
            "source": contact.source,
        }
        await send_email(
            to=agent.email,
            subject=f"New contact: {contact.full_name}",
            body=context,
        )
