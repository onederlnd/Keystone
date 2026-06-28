# tests/test_auth.py

import pytest


@pytest.mark.asyncio
async def test_register(client):
    response = await client.post(
        "/auth/register",
        json={
            "email": "new@test.com",
            "password": "password123",
            "full_name": "New User",
        },
    )
    assert response.status_code == 201
    assert response.json()["email"] == "new@test.com"


@pytest.mark.asyncio
async def test_register_duplicate_email(client, create_user_in_db):
    await create_user_in_db(email="dupe@test.com")
    response = await client.post(
        "/auth/register",
        json={
            "email": "dupe@test.com",
            "password": "password123",
            "full_name": "Dupe User",
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login(client, create_user_in_db):
    await create_user_in_db(email="login@test.com", password="password123")
    response = await client.post(
        "/auth/login", json={"email": "login@test.com", "password": "password123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_login_bad_credentials(client, create_user_in_db):
    await create_user_in_db(email="bad@test.com", password="password123")
    response = await client.post(
        "/auth/login", json={"email": "bad@test.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_token_rejection(client):
    response = await client.get(
        "/users/me", headers={"Authorization": "Bearer faketoken"}
    )
    assert response.status_code == 401
