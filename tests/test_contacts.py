# tests/test_contacts.py

import uuid
import pytest
from sqlalchemy import select

from backend.app.models.user import UserRole
from backend.app.models.contact import Contacts
from backend.app.core.security import create_access_token


def _headers_for(user):
    token = create_access_token({"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_contact(client, create_user_in_db):
    agent = await create_user_in_db(email="agent1@test.com", role=UserRole.agent)
    response = await client.post(
        "/contacts/",
        json={
            "agent_id": str(agent.id),
            "user_id": str(agent.id),
            "full_name": "New Lead",
            "email": "lead@test.com",
            "phone": "555-0111",
            "type": "buyer",
            "source": "referral",
        },
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "New Lead"


@pytest.mark.asyncio
async def test_get_contact_owner_can_access(client, create_contact_in_db):
    contact, agent = await create_contact_in_db()
    response = await client.get(f"/contacts/{contact.id}", headers=_headers_for(agent))
    assert response.status_code == 200
    assert response.json()["id"] == str(contact.id)


@pytest.mark.asyncio
async def test_get_contact_non_owner_forbidden(
    client, create_contact_in_db, create_user_in_db
):
    contact, agent = await create_contact_in_db()
    other_agent = await create_user_in_db(
        email="otheragent@test.com", role=UserRole.agent
    )
    response = await client.get(
        f"/contacts/{contact.id}", headers=_headers_for(other_agent)
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_contact_admin_can_access_any(
    client, create_contact_in_db, create_user_in_db
):
    contact, agent = await create_contact_in_db()
    admin = await create_user_in_db(email="admin1@test.com", role=UserRole.admin)
    response = await client.get(f"/contacts/{contact.id}", headers=_headers_for(admin))
    assert response.status_code == 200
    assert response.json()["id"] == str(contact.id)


@pytest.mark.asyncio
async def test_get_contact_not_found(client, create_user_in_db):
    agent = await create_user_in_db(email="agent2@test.com", role=UserRole.agent)
    response = await client.get(
        f"/contacts/{uuid.uuid4()}", headers=_headers_for(agent)
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_contact_owner(client, create_contact_in_db):
    contact, agent = await create_contact_in_db()
    response = await client.patch(
        f"/contacts/{contact.id}",
        json={"full_name": "Updated Name"},
        headers=_headers_for(agent),
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Name"


@pytest.mark.asyncio
async def test_update_contact_non_owner_forbidden(
    client, create_contact_in_db, create_user_in_db
):
    contact, agent = await create_contact_in_db()
    other_agent = await create_user_in_db(
        email="otheragent2@test.com", role=UserRole.agent
    )
    response = await client.patch(
        f"/contacts/{contact.id}",
        json={"full_name": "Hijacked Name"},
        headers=_headers_for(other_agent),
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_archive_contact_owner(client, create_contact_in_db, db_session):
    contact, agent = await create_contact_in_db()
    response = await client.patch(
        f"/contacts/{contact.id}/archive", headers=_headers_for(agent)
    )
    assert response.status_code == 200

    result = await db_session.execute(select(Contacts).where(Contacts.id == contact.id))
    updated = result.scalar_one_or_none()
    assert updated.is_archived is True


@pytest.mark.asyncio
async def test_archive_contact_non_owner_forbidden(
    client, create_contact_in_db, create_user_in_db
):
    contact, agent = await create_contact_in_db()
    other_agent = await create_user_in_db(
        email="otheragent3@test.com", role=UserRole.agent
    )
    response = await client.patch(
        f"/contacts/{contact.id}/archive", headers=_headers_for(other_agent)
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_contacts_scoped_to_own_agent(
    client, create_contact_in_db, create_user_in_db
):
    agent_a = await create_user_in_db(email="agenta@test.com", role=UserRole.agent)
    agent_b = await create_user_in_db(email="agentb@test.com", role=UserRole.agent)

    contact_a, _ = await create_contact_in_db(agent=agent_a)
    await create_contact_in_db(agent=agent_b)

    response = await client.get("/contacts/", headers=_headers_for(agent_a))
    assert response.status_code == 200
    ids = [c["id"] for c in response.json()]
    assert str(contact_a.id) in ids
    assert len(ids) == 1


@pytest.mark.asyncio
async def test_list_contacts_admin_sees_all(
    client, create_contact_in_db, create_user_in_db
):
    agent_a = await create_user_in_db(email="agentc@test.com", role=UserRole.agent)
    agent_b = await create_user_in_db(email="agentd@test.com", role=UserRole.agent)
    admin = await create_user_in_db(email="admin2@test.com", role=UserRole.admin)

    await create_contact_in_db(agent=agent_a)
    await create_contact_in_db(agent=agent_b)

    response = await client.get("/contacts/", headers=_headers_for(admin))
    assert response.status_code == 200
    assert len(response.json()) >= 2


@pytest.mark.asyncio
async def test_list_contacts_type_filter(
    client, create_contact_in_db, create_user_in_db
):
    agent = await create_user_in_db(email="agente@test.com", role=UserRole.agent)
    await create_contact_in_db(agent=agent, type="buyer")
    await create_contact_in_db(agent=agent, type="seller")

    response = await client.get("/contacts/?type=seller", headers=_headers_for(agent))
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["type"] == "seller"
