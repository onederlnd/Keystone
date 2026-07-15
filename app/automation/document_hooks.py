# app/automation/document_hooks.py

import uuid
from sqlalchemy import select
from app.automation.hooks import register_hook
from app.core.database import AsyncSessionLocal
from app.models.listing import Listings
from app.models.user import Users
from app.services.document import _generate_and_queue_document


async def on_listing_active(context: dict):
    """Generates listing agreement"""
    async with AsyncSessionLocal() as db:
        listing_result = await db.execute(
            select(Listings).where(Listings.id == uuid.UUID(context["listing_id"]))
        )
        listing = listing_result.scalar_one_or_none()

        agent_result = await db.execute(
            select(Users).where(Users.id == listing.agent_id)
        )
        agent = agent_result.scalar_one_or_none()

        await _generate_and_queue_document(
            db,
            template_name="listing_agreement",
            listing=listing,
            agent=agent,
            doc_type="listing_agreement",
            contact=None,
            pipeline=None,
            created_by_id=listing.agent_id,
        )


async def on_document_sent(context):
    print(f"[HOOK] document.sent | {context}")


register_hook("listing.active", on_listing_active)
register_hook("document.sent", on_document_sent)
