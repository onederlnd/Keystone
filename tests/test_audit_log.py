# tests/test_audit_log.py

import pytest
from app.models.audit_log import AuditLog


@pytest.mark.asyncio
async def test_audit_log_written_on_user_creation(client):
    response = await client.post(
        "/auth/register",
        json={
            "email": "audit@test.com",
            "password": "password123",
            "full_name": "Audit User",
        },
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_audit_log_entity_type_and_action(client, db_session):
    from sqlalchemy import select

    response = await client.post(
        "/auth/register",
        json={
            "email": "auditcheck@test.com",
            "password": "password123",
            "full_name": "Audit User",
        },
    )
    assert response.status_code == 201
    user_id = response.json()["id"]
    result = await db_session.execute(
        select(AuditLog).where(AuditLog.entity_id == user_id)
    )
    log = result.scalar_one_or_none()
    assert log is not None
    assert log.entity_type == "user"
    assert log.action == "created"
    assert log.actor_id is None
