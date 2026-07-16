# app/tasks/email_tasks.py

from sqlalchemy import select

from app.core.celery_app import async_task
from app.core.database import AsyncSessionLocal
from app.core.notifications import send_email
from app.models.listing import Listings
from app.models.document import Documents
from app.models.pipeline import Pipelines
from app.models.contact import Contacts

LISTING_ROLES = {"agent", "seller"}
PIPELINE_ROLES = {"agent", "contact"}


# TODO:
# Fix _resolve_recipient OR call sites — currently mismatched (helper expects flat set, call passes dict)
def _resolve_recipient(entity, recipient_role, allowed_roles):
    if recipient_role not in allowed_roles:
        return None
    return getattr(entity, recipient_role, None)


@async_task(name="tasks.send_listing_status_email")
async def send_listing_status_email(listing_id, recipient_role):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Listings).where(Listings.id == listing_id))

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


@async_task(name="tasks.send_document_ready_email")
async def send_document_ready_email(document_id):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Documents).where(Documents.id == document_id))

        document = result.scalar_one_or_none()
        if not document:
            return

        recipient = document.contact or document.created_by
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


@async_task(name="tasks.send_pipeline_stage_email")
async def send_pipeline_stage_email(pipeline_id, recipient_role):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Pipelines).where(Pipelines.id == pipeline_id))

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


# send_new_contact_email(contact_id) # sending to contact.agent
@async_task(name="tasks.send_new_contact_email")
async def send_new_contact_email(contact_id):
    # sends to contact_id.agent
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Contacts).where(Contacts.id == contact_id))

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
