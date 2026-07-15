# app/tasks/email_tasks.py

from sqlalchemy import select

from app.tasks.celery_app import async_task
from app.core.database import AsyncSessionLocal
from app.core.notifications import send_email
from app.models.listing import Listings
from app.models.document import Documents
from app.models.pipeline import Pipelines


@async_task(name="tasks.send_listing_status_email")
async def send_listing_status_email(listing_id):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Listings).where(Listings.id == listing_id))
        listing = result.scalar_one_or_none()

        if not listing:
            return

        context = {
            "address": listing.address,
            "status": listing.status,
            "price": listing.price,
        }

        await send_email(
            to=listing.seller.email,
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

        context = {
            "type": document.type,
            "status": document.status,
        }

        await send_email(
            to=document.created_by.email,
            subject=f"Document ready: {document.type}",
            body=context,
        )


@async_task(name="tasks.send_pipeline_stage_email")
async def send_pipeline_stage_email(pipeline_id):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Pipelines).where(Pipelines.id == pipeline_id))
        pipeline = result.scalar_one_or_none()

        if not pipeline:
            return

        context = {
            "stage": pipeline.stage,
            "offer_price": pipeline.offer_price,
        }

        await send_email(
            to=pipeline.agent.email,
            subject=f"Pipeline update: {pipeline.stage}",
            body=context,
        )
