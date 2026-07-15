# tests/test_listing_hooks.py

from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select

from backend.app.models.listing_status_history import ListingStatusHistory
from backend.app.models.approval_queue import ApprovalQueue
from backend.app.core.config import settings


@pytest.mark.asyncio
async def test_status_change_fires_hook_with_correct_event_and_context(
    client, create_listing_in_db, create_user_in_db, monkeypatch
):
    mock_fire_hook = AsyncMock()
    monkeypatch.setattr("backend.app.services.listing.fire_hook", mock_fire_hook)

    listing = await create_listing_in_db()
    agent = await create_user_in_db(email="hookagent@test.com")

    response = await client.patch(
        f"/listings/{listing.id}/status",
        json={
            "new_status": "active",
            "changed_by_id": str(agent.id),
            "triggered_by": "manual",
        },
    )

    assert response.status_code == 200
    mock_fire_hook.assert_called_once()

    event_name, context = mock_fire_hook.call_args.args
    assert event_name == "listing.active"
    assert context["new_status"] == "active"
    assert context["changed_by_id"] == str(agent.id)


@pytest.mark.asyncio
async def test_automation_disabled_hook_is_noop(
    client, create_listing_in_db, create_user_in_db, monkeypatch
):
    monkeypatch.setattr(settings, "automation_enabled", False)

    side_effect_spy = AsyncMock()
    from backend.app.automation.hooks import register_hook

    register_hook("listing.active", side_effect_spy)

    listing = await create_listing_in_db()
    agent = await create_user_in_db(email="noopagent@test.com")

    response = await client.patch(
        f"/listings/{listing.id}/status",
        json={
            "new_status": "active",
            "changed_by_id": str(agent.id),
            "triggered_by": "manual",
        },
    )

    assert response.status_code == 200
    side_effect_spy.assert_not_called()


@pytest.mark.asyncio
async def test_approval_required_transition_automation_does_not_write_history(
    client, create_listing_in_db, create_user_in_db, db_session
):
    listing = await create_listing_in_db()
    agent = await create_user_in_db(email="approvalagent1@test.com")

    # activate first so we can attempt an approval-required transition
    await client.patch(
        f"/listings/{listing.id}/status",
        json={
            "new_status": "active",
            "changed_by_id": str(agent.id),
            "triggered_by": "manual",
        },
    )

    response = await client.patch(
        f"/listings/{listing.id}/status",
        json={
            "new_status": "pending",
            "changed_by_id": str(agent.id),
            "triggered_by": "automation",
        },
    )
    assert response.status_code == 200

    history_result = await db_session.execute(
        select(ListingStatusHistory).where(
            ListingStatusHistory.listing_id == listing.id,
            ListingStatusHistory.new_status == "pending",
        )
    )
    assert history_result.scalars().all() == []

    queue_result = await db_session.execute(
        select(ApprovalQueue).where(ApprovalQueue.entity_id == str(listing.id))
    )
    queue_entries = queue_result.scalars().all()
    assert len(queue_entries) == 1
    assert queue_entries[0].proposed_state == "pending"


@pytest.mark.asyncio
async def test_approval_required_transition_manual_also_queues(
    client, create_listing_in_db, create_user_in_db, db_session
):
    listing = await create_listing_in_db()
    agent = await create_user_in_db(email="approvalagent2@test.com")

    await client.patch(
        f"/listings/{listing.id}/status",
        json={
            "new_status": "active",
            "changed_by_id": str(agent.id),
            "triggered_by": "manual",
        },
    )

    response = await client.patch(
        f"/listings/{listing.id}/status",
        json={
            "new_status": "pending",
            "changed_by_id": str(agent.id),
            "triggered_by": "manual",
        },
    )
    assert response.status_code == 200

    history_result = await db_session.execute(
        select(ListingStatusHistory).where(
            ListingStatusHistory.listing_id == listing.id,
            ListingStatusHistory.new_status == "pending",
        )
    )
    assert history_result.scalars().all() == []

    queue_result = await db_session.execute(
        select(ApprovalQueue).where(ApprovalQueue.entity_id == str(listing.id))
    )
    queue_entries = queue_result.scalars().all()
    assert len(queue_entries) == 1
    assert queue_entries[0].created_by == str(agent.id)
