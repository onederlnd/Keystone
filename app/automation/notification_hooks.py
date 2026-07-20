# app/automation/notification_hooks.py

from app.automation.hooks import register_hook
from app.core.dedup import is_duplicate
from app.tasks.email_tasks import (
    send_listing_status_email,
    send_pipeline_stage_email,
    send_document_ready_email,
    send_new_contact_email,
)


async def on_listing_active(context):
    listing_id = context["listing_id"]
    for role in ["agent", "seller"]:
        if await is_duplicate(f"listing.active:{role}", listing_id, "active"):
            continue
        send_listing_status_email.delay(listing_id, role, entity_type="listing")


async def on_listing_under_contract(context):
    listing_id = context["listing_id"]
    for role in ["agent", "buyer", "seller"]:
        if await is_duplicate(
            f"listing.under_contract:{role}", listing_id, "under_contract"
        ):
            continue
        send_listing_status_email.delay(listing_id, role, entity_type="listing")


async def on_listing_sold(context):
    listing_id = context["listing_id"]
    for role in ["agent", "buyer", "seller"]:
        if await is_duplicate(f"listing.sold:{role}", listing_id, "sold"):
            continue
        send_listing_status_email.delay(listing_id, role, entity_type="listing")


async def on_listing_stale(context):
    listing_id = context["listing_id"]
    if await is_duplicate("listing.stale:agent", listing_id, "stale"):
        return
    send_listing_status_email.delay(listing_id, "agent", entity_type="listing")


async def on_pipeline_offer_submitted(context):
    pipeline_id = context["pipeline_id"]
    for role in ["agent", "contact"]:
        if await is_duplicate(
            f"pipeline.offer_submitted:{role}", pipeline_id, "offer_submitted"
        ):
            continue
        send_pipeline_stage_email.delay(pipeline_id, role, entity_type="pipeline")


async def on_pipeline_closed(context):
    pipeline_id = context["pipeline_id"]
    for role in ["agent", "contact"]:
        if await is_duplicate(f"pipeline.closed:{role}", pipeline_id, "closed"):
            continue
        send_pipeline_stage_email.delay(pipeline_id, role, entity_type="pipeline")


async def on_document_sent(context):
    document_id = context["document_id"]
    if await is_duplicate("document.sent", document_id, "sent"):
        return
    send_document_ready_email.delay(document_id, entity_type="document")


async def on_contact_created(context):
    contact_id = context["contact_id"]
    if await is_duplicate("contact.created", contact_id, "created"):
        return
    send_new_contact_email.delay(contact_id, entity_type="contact")


register_hook("listing.active", on_listing_active)
register_hook("listing.under_contract", on_listing_under_contract)
register_hook("listing.sold", on_listing_sold)
register_hook("listing.stale", on_listing_stale)
register_hook("pipeline.offer_submitted", on_pipeline_offer_submitted)
register_hook("pipeline.closed", on_pipeline_closed)
register_hook("document.sent", on_document_sent)
register_hook("contact.created", on_contact_created)
