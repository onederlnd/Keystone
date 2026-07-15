import uuid
from sqlalchemy import select
from backend.app.models.approval_queue import ApprovalQueue
from backend.app.models.listing import Listings
from backend.app.automation.hooks import register_hook
from backend.app.core.database import AsyncSessionLocal


async def on_listing_active(context):
    async with AsyncSessionLocal() as db:
        pass


async def on_listing_under_contract(context):
    async with AsyncSessionLocal() as db:
        pass


async def on_listing_sold(context):
    async with AsyncSessionLocal() as db:
        pass


async def on_listing_stale(context):
    async with AsyncSessionLocal() as db:
        pass


async def on_pipeline_offer_submitted(context):
    async with AsyncSessionLocal() as db:
        pass


async def on_pipeline_closed(context):
    async with AsyncSessionLocal() as db:
        pass


async def on_document_sent(context):
    async with AsyncSessionLocal() as db:
        pass


async def on_contact_created(context):
    async with AsyncSessionLocal() as db:
        pass


register_hook("listing.active", on_listing_active)
register_hook("listing.under_contract", on_listing_under_contract)
register_hook("listing.sold", on_listing_sold)
register_hook("listing.stale", on_listing_stale)
register_hook("pipeline.offer_submitted", on_pipeline_offer_submitted)
register_hook("pipeline.closed", on_pipeline_closed)
register_hook("document.sent", on_document_sent)
register_hook("contact.created", on_contact_created)
