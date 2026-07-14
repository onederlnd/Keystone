# tests/test_pipeline.py

import uuid
import pytest
from sqlalchemy import select

from backend.app.models.user import UserRole
from backend.app.models.pipeline import Pipelines
from backend.app.models.approval_queue import ApprovalQueue


@pytest.mark.asyncio
async def test_add_to_pipeline(
    client, create_listing_in_db, create_user_in_db, create_contact_in_db
):
    listing = await create_listing_in_db()
    agent = await create_user_in_db(email="pipeagent1@test.com", role=UserRole.agent)
    contact, _ = await create_contact_in_db(agent=agent)

    response = await client.post(
        "/pipeline/",
        json={
            "listing_id": str(listing.id),
            "contact_id": str(contact.id),
            "agent_id": str(agent.id),
            "stage": "new",
        },
    )
    assert response.status_code == 200
    assert response.json()["stage"] == "new"


@pytest.mark.asyncio
async def test_add_to_pipeline_duplicate_rejected(
    client, create_listing_in_db, create_user_in_db, create_contact_in_db
):
    listing = await create_listing_in_db()
    agent = await create_user_in_db(email="pipeagent2@test.com", role=UserRole.agent)
    contact, _ = await create_contact_in_db(agent=agent)

    payload = {
        "listing_id": str(listing.id),
        "contact_id": str(contact.id),
        "agent_id": str(agent.id),
        "stage": "new",
    }
    first = await client.post("/pipeline/", json=payload)
    assert first.status_code == 200

    second = await client.post("/pipeline/", json=payload)
    assert second.status_code == 400


@pytest.mark.asyncio
async def test_get_pipeline_entry(client, create_pipeline_in_db):
    entry = await create_pipeline_in_db()
    response = await client.get(f"/pipeline/{entry.id}")
    assert response.status_code == 200
    assert response.json()["id"] == str(entry.id)


@pytest.mark.asyncio
async def test_get_pipeline_entry_not_found(client):
    response = await client.get(f"/pipeline/{uuid.uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_pipeline_filter_by_stage(client, create_pipeline_in_db):
    await create_pipeline_in_db(stage="new")
    await create_pipeline_in_db(stage="contacted")

    response = await client.get("/pipeline/?stage=contacted")
    assert response.status_code == 200
    results = response.json()
    assert all(p["stage"] == "contacted" for p in results)
    assert len(results) == 1


@pytest.mark.asyncio
async def test_valid_stage_transition_applies(
    client, create_pipeline_in_db, db_session
):
    entry = await create_pipeline_in_db(stage="new")

    response = await client.patch(
        f"/pipeline/{entry.id}",
        json={"stage": "contacted"},
    )
    assert response.status_code == 200
    assert response.json()["stage"] == "contacted"

    result = await db_session.execute(select(Pipelines).where(Pipelines.id == entry.id))
    updated = result.scalar_one_or_none()
    assert updated.stage == "contacted"
    assert updated.last_stage_change_at is not None


@pytest.mark.asyncio
async def test_invalid_stage_transition_rejected(client, create_pipeline_in_db):
    entry = await create_pipeline_in_db(stage="new")

    response = await client.patch(
        f"/pipeline/{entry.id}",
        json={"stage": "closed"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_approval_required_transition_does_not_apply_stage(
    client, create_pipeline_in_db, db_session
):
    entry = await create_pipeline_in_db(stage="under_contract")

    response = await client.patch(
        f"/pipeline/{entry.id}",
        json={"stage": "closed"},
    )
    assert response.status_code == 200
    assert response.json()["stage"] == "under_contract"  # unchanged

    result = await db_session.execute(
        select(ApprovalQueue).where(ApprovalQueue.entity_id == str(entry.id))
    )
    queue_entries = result.scalars().all()
    assert len(queue_entries) == 1
    assert queue_entries[0].proposed_state == "closed"


@pytest.mark.asyncio
async def test_remove_pipeline_entry(client, create_pipeline_in_db, db_session):
    entry = await create_pipeline_in_db()

    response = await client.patch(f"/pipeline/{entry.id}/remove")
    assert response.status_code == 200

    result = await db_session.execute(select(Pipelines).where(Pipelines.id == entry.id))
    assert result.scalar_one_or_none() is None
