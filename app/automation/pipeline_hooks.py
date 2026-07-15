# app/automation/pipeline_hooks.py

import uuid
from app.automation.hooks import register_hook
from sqlalchemy import select
from app.models.listing import Listings
from app.models.user import Users
from app.models.contact import Contacts
from app.models.pipeline import Pipelines
from app.core.database import AsyncSessionLocal
from app.services.document import _generate_and_queue_document


async def on_pipeline_offer_submitted(context):
    """Generates offer letter, queues for review"""
    async with AsyncSessionLocal() as db:
        pipeline_result = await db.execute(
            select(Pipelines).where(Pipelines.id == uuid.UUID(context["pipeline_id"]))
        )
        pipeline = pipeline_result.scalar_one_or_none()

        listing_result = await db.execute(
            select(Listings).where(Listings.id == pipeline.listing_id)
        )
        listing = listing_result.scalar_one_or_none()

        contact_results = await db.execute(
            select(Contacts).where(Contacts.id == pipeline.contact_id)
        )
        contact = contact_results.scalar_one_or_none()

        agent_result = await db.execute(
            select(Users).where(Users.id == listing.agent_id)
        )
        agent = agent_result.scalar_one_or_none()

        await _generate_and_queue_document(
            db,
            template_name="offer_letter",
            listing=listing,
            agent=agent,
            doc_type="offer_letter",
            contact=contact,
            pipeline=pipeline,
            created_by_id=listing.agent_id,
        )


async def on_pipeline_closed(context):
    """Generates closing summary, queue for revew"""
    async with AsyncSessionLocal() as db:
        pipeline_result = await db.execute(
            select(Pipelines).where(Pipelines.id == uuid.UUID(context["pipeline_id"]))
        )
        pipeline = pipeline_result.scalar_one_or_none()

        listing_result = await db.execute(
            select(Listings).where(Listings.id == pipeline.listing_id)
        )
        listing = listing_result.scalar_one_or_none()

        contact_results = await db.execute(
            select(Contacts).where(Contacts.id == pipeline.contact_id)
        )
        contact = contact_results.scalar_one_or_none()

        agent_result = await db.execute(
            select(Users).where(Users.id == listing.agent_id)
        )
        agent = agent_result.scalar_one_or_none()

        await _generate_and_queue_document(
            db,
            template_name="closing_summary",
            listing=listing,
            agent=agent,
            doc_type="closing_summary",
            contact=contact,
            pipeline=pipeline,
            created_by_id=listing.agent_id,
        )


async def on_pipeline_lost(context):
    print(f"[HOOK] pipeline.lost | {context}")


register_hook("pipeline.offer_submitted", on_pipeline_offer_submitted)
register_hook("pipeline.closed", on_pipeline_closed)
register_hook("pipeline.lost", on_pipeline_lost)
