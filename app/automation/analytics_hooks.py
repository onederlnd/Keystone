import uuid
from sqlalchemy import select
from app.models.approval_queue import ApprovalQueue
from app.models.listing import Listings
from app.automation.hooks import register_hook
from app.core.database import AsyncSessionLocal


async def on_listing_stale(context):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Listings).where(Listings.id == uuid.UUID(context["listing_id"]))
        )
        listing = result.scalar_one_or_none()
        if listing is None:
            return

        entry = ApprovalQueue(
            entity_type="listing",
            entity_id=str(listing.id),
            proposed_action="review_stale_listing",
            proposed_state=None,
            context={
                "listing_id": str(listing.id),
                "note": "Consider reducing price or archiving",
            },
            status="pending",
            created_by="automation",
        )

        db.add(entry)
        await db.commit()


async def on_listing_price_alert(context):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Listings).where(Listings.id == uuid.UUID(context["listing_id"]))
        )
        listing = result.scalar_one_or_none()
        if listing is None:
            return

        entry = ApprovalQueue(
            entity_type="listing",
            entity_id=str(listing.id),
            proposed_action="review_price_alert",
            proposed_state=None,
            context={
                "listing_id": str(listing.id),
                "percent_diff": context["percent_diff"],
            },
            status="pending",
            created_by="automation",
        )

        db.add(entry)
        await db.commit()


register_hook("listing.stale", on_listing_stale)
register_hook("listing.price_alert", on_listing_price_alert)
