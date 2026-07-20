# tests/test_analytics_hooks.py

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.core.config import settings
from app.automation.hooks import fire_hook
from app.models.approval_queue import ApprovalQueue
from app.models.listing_status_history import ListingStatusHistory


@pytest_asyncio.fixture(autouse=True)
async def register_hooks_for_test(reset_hook_registry, monkeypatch):
    """
    Same reload approach as test_document_hooks.py's fixture — reload if
    already imported, otherwise import fresh. Avoids double-registration on
    the first test that touches this module in the whole session.
    """
    import sys
    import importlib
    from tests.conftest import TestSessionLocal

    for name in ("app.automation.analytics_hooks",):
        if name in sys.modules:
            importlib.reload(sys.modules[name])
        else:
            importlib.import_module(name)

    monkeypatch.setattr(
        "app.automation.analytics_hooks.AsyncSessionLocal", TestSessionLocal
    )

    yield


async def _add_history(db_session, listing_id, new_status, changed_at, changed_by_id):
    row = ListingStatusHistory(
        listing_id=listing_id,
        previous_status="draft",
        new_status=new_status,
        changed_by_id=changed_by_id,
        notes=None,
        triggered_by="manual",
        changed_at=changed_at,
    )
    db_session.add(row)
    await db_session.commit()
    await db_session.refresh(row)
    return row


@pytest.mark.asyncio
async def test_listing_stale_hook_writes_approval_queue_entry(
    db_session, create_listing_in_db, patch_async_session_local
):
    listing = await create_listing_in_db(status="active")

    with patch_object_automation_enabled(True):
        await fire_hook("listing.stale", {"listing_id": str(listing.id)})

    result = await db_session.execute(
        select(ApprovalQueue).where(ApprovalQueue.entity_id == str(listing.id))
    )
    entry = result.scalar_one_or_none()

    assert entry is not None
    assert entry.entity_type == "listing"
    assert entry.proposed_action == "review_stale_listing"
    assert entry.status == "pending"
    assert entry.created_by == "automation"
    assert entry.context["listing_id"] == str(listing.id)


@pytest.mark.asyncio
async def test_listing_price_alert_hook_writes_approval_queue_entry_with_percent_diff(
    db_session, create_listing_in_db, patch_async_session_local
):
    listing = await create_listing_in_db(status="active")

    with patch_object_automation_enabled(True):
        await fire_hook(
            "listing.price_alert",
            {"listing_id": str(listing.id), "percent_diff": 42.5},
        )

    result = await db_session.execute(
        select(ApprovalQueue).where(ApprovalQueue.entity_id == str(listing.id))
    )
    entry = result.scalar_one_or_none()

    assert entry is not None
    assert entry.proposed_action == "review_price_alert"
    assert entry.context["percent_diff"] == 42.5


@pytest.mark.asyncio
async def test_stale_hook_noop_when_automation_disabled(
    db_session, create_listing_in_db
):
    listing = await create_listing_in_db(status="active")

    with patch_object_automation_enabled(False):
        await fire_hook("listing.stale", {"listing_id": str(listing.id)})

    result = await db_session.execute(
        select(ApprovalQueue).where(ApprovalQueue.entity_id == str(listing.id))
    )
    assert result.scalar_one_or_none() is None


def patch_object_automation_enabled(value):
    from unittest.mock import patch

    return patch.object(settings, "automation_enabled", value)
