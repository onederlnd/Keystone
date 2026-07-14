# tests/test_listings.py

import pytest
from backend.app.models.user import UserRole


@pytest.mark.asyncio
async def test_create_listing(client, create_user_in_db):
    agent = await create_user_in_db(email="agent@test.com", role=UserRole.agent)
    seller = await create_user_in_db(email="seller@test.com", role=UserRole.seller)
    response = await client.post(
        "/listings/",
        json={
            "agent_id": str(agent.id),
            "seller_id": str(seller.id),
            "address": "123 Main St",
            "city": "Detroit",
            "state": "MI",
            "zip": "48201",
            "price": 250000,
            "bedrooms": 3,
            "bathrooms": 2,
            "sqft": 1500,
            "mls_id": "MLS123",
        },
    )
    assert response.status_code == 200
    assert response.json()["address"] == "123 Main St"


@pytest.mark.asyncio
async def test_get_listing(client, create_listing_in_db):
    listing = await create_listing_in_db()
    response = await client.get(f"/listings/{listing.id}")
    assert response.status_code == 200
    assert response.json()["id"] == str(listing.id)


@pytest.mark.asyncio
async def test_get_listing_not_found(client):
    import uuid

    response = await client.get(f"/listings/{uuid.uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_listings(client, create_listing_in_db):
    await create_listing_in_db()
    response = await client.get("/listings/")
    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.asyncio
async def test_list_listings_filter_city(client, create_listing_in_db):
    await create_listing_in_db()
    response = await client.get("/listings/?city=Detroit")
    assert response.status_code == 200
    assert all(l["city"] == "Detroit" for l in response.json())


@pytest.mark.asyncio
async def test_list_listings_filter_price(client, create_listing_in_db):
    await create_listing_in_db()
    response = await client.get("/listings/?min_price=100000&max_price=300000")
    assert response.status_code == 200
    assert all(100000 <= l["price"] <= 300000 for l in response.json())


@pytest.mark.asyncio
async def test_update_listing(client, create_listing_in_db):
    listing = await create_listing_in_db()
    response = await client.patch(f"/listings/{listing.id}", json={"price": 300000})
    assert response.status_code == 200
    assert response.json()["price"] == 300000


@pytest.mark.asyncio
async def test_update_listing_not_found(client):
    import uuid

    response = await client.patch(f"/listings/{uuid.uuid4()}", json={"price": 300000})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_archive_listing(client, create_listing_in_db):
    listing = await create_listing_in_db()
    response = await client.patch(f"/listings/{listing.id}/archive")
    assert response.status_code == 200
    assert response.json()["status"] == "archived"


@pytest.mark.asyncio
async def test_change_status_valid(client, create_listing_in_db, create_user_in_db):
    listing = await create_listing_in_db()
    agent = await create_user_in_db(email="agent2@test.com", role=UserRole.agent)
    response = await client.patch(
        f"/listings/{listing.id}/status",
        json={
            "new_status": "active",
            "changed_by_id": str(agent.id),
            "triggered_by": "manual",
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "active"


@pytest.mark.asyncio
async def test_change_status_invalid_transition(
    client, create_listing_in_db, create_user_in_db
):
    listing = await create_listing_in_db()
    agent = await create_user_in_db(email="agent3@test.com", role=UserRole.agent)
    response = await client.patch(
        f"/listings/{listing.id}/status",
        json={
            "new_status": "sold",
            "changed_by_id": str(agent.id),
            "triggered_by": "manual",
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_change_status_requires_approval(
    client, create_listing_in_db, create_user_in_db, db_session
):
    from backend.app.models.approval_queue import ApprovalQueue
    from sqlalchemy import select

    listing = await create_listing_in_db()
    agent = await create_user_in_db(email="agent4@test.com", role=UserRole.agent)
    # First activate the listing
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
    result = await db_session.execute(select(ApprovalQueue))
    queue = result.scalars().all()
    assert len(queue) >= 1


@pytest.mark.asyncio
async def test_get_status_history(client, create_listing_in_db, create_user_in_db):
    listing = await create_listing_in_db()
    agent = await create_user_in_db(email="agent5@test.com", role=UserRole.agent)
    await client.patch(
        f"/listings/{listing.id}/status",
        json={
            "new_status": "active",
            "changed_by_id": str(agent.id),
            "triggered_by": "manual",
        },
    )
    response = await client.get(f"/listings/{listing.id}/status-history")
    assert response.status_code == 200
    assert len(response.json()) >= 1
