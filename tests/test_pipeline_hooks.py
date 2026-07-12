# tests/test_pipeline_hooks.py

from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock
import pytest
from sqlalchemy import select
from app.models.approval_queue import ApprovalQueue
from app.services.pipeline import get_stale_pipeline_entries


@pytest.mark.asyncio
async def test_offer_submitted_fires_correct_hook(
    client, create_pipeline_in_db, monkeypatch
):
    mock_fire_hook = AsyncMock()
    monkeypatch.setattr("app.services.pipeline.fire_hook", mock_fire_hook)

    entry = await create_pipeline_in_db(stage="showing_scheduled")

    response = await client.patch(
        f"/pipeline/{entry.id}",
        json={"stage": "offer_submitted"},
    )
    assert response.status_code == 200

    mock_fire_hook.assert_called_once()
    event_name, context = mock_fire_hook.call_args.args
    assert event_name == "pipeline.offer_submitted"
    assert context["to_stage"] == "offer_submitted"


@pytest.mark.asyncio
async def test_closed_transition_queues_for_approval_no_hook_fired(
    client, create_pipeline_in_db, db_session, monkeypatch
):
    mock_fire_hook = AsyncMock()
    monkeypatch.setattr("app.services.pipeline.fire_hook", mock_fire_hook)

    entry = await create_pipeline_in_db(stage="under_contract")

    response = await client.patch(
        f"/pipeline/{entry.id}",
        json={"stage": "closed"},
    )
    assert response.status_code == 200
    assert response.json()["stage"] == "under_contract"  # unchanged, pending approval

    mock_fire_hook.assert_not_called()

    result = await db_session.execute(
        select(ApprovalQueue).where(ApprovalQueue.entity_id == str(entry.id))
    )
    queue_entries = result.scalars().all()
    assert len(queue_entries) == 1
    assert queue_entries[0].proposed_state == "closed"
    assert queue_entries[0].proposed_action == "stage_change"


@pytest.mark.asyncio
async def test_stale_detection_returns_correct_entries(
    db_session, create_pipeline_in_db
):
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    stale_entry = await create_pipeline_in_db(stage="contacted")
    stale_entry.last_stage_change_at = now - timedelta(days=10)
    db_session.add(stale_entry)

    fresh_entry = await create_pipeline_in_db(stage="contacted")
    fresh_entry.last_stage_change_at = now - timedelta(days=1)
    db_session.add(fresh_entry)

    await db_session.commit()

    results = await get_stale_pipeline_entries(db_session, days_threshold=5)
    result_ids = [r.id for r in results]

    assert stale_entry.id in result_ids
    assert fresh_entry.id not in result_ids


@pytest.mark.asyncio
async def test_approval_required_transition_manual_and_automation_both_queue(
    client, create_pipeline_in_db, db_session
):
    entry_manual = await create_pipeline_in_db(stage="under_contract")
    entry_auto = await create_pipeline_in_db(stage="under_contract")

    resp_manual = await client.patch(
        f"/pipeline/{entry_manual.id}",
        json={"stage": "closed"},
    )
    assert resp_manual.status_code == 200

    resp_auto = await client.patch(
        f"/pipeline/{entry_auto.id}",
        json={"stage": "closed"},
    )
    assert resp_auto.status_code == 200

    result = await db_session.execute(
        select(ApprovalQueue).where(
            ApprovalQueue.entity_id.in_([str(entry_manual.id), str(entry_auto.id)])
        )
    )
    queue_entries = result.scalars().all()
    assert len(queue_entries) == 2
