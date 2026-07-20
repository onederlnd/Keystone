# tests/test_auth.py

import pytest
import pytest_asyncio
from app.core.limiter import limiter


@pytest_asyncio.fixture
async def reset_limiter():
    limiter.reset()
    yield
    limiter.reset()


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


@pytest.mark.asyncio
async def test_repeated_failed_logins_are_rate_limited(
    client, create_user_in_db, reset_limiter
):
    await create_user_in_db(email="ratelimit@test.com", password="password123")

    payload = {"email": "ratelimit@test.com", "password": "wrongpassword"}

    responses = []
    for _ in range(6):
        response = await client.post("/auth/login", json=payload)
        responses.append(response.status_code)

    assert responses[:5] == [401, 401, 401, 401, 401]
    assert responses[5] == 429


@pytest.mark.asyncio
async def test_login_failure_message_same_for_bad_email_and_bad_password(
    client, create_user_in_db, reset_limiter
):
    await create_user_in_db(email="realuser@test.com", password="correctpassword")

    bad_email_response = await client.post(
        "/auth/login",
        json={"email": "doesnotexist@test.com", "password": "whatever"},
    )
    bad_password_response = await client.post(
        "/auth/login",
        json={"email": "realuser@test.com", "password": "wrongpassword"},
    )

    assert bad_email_response.status_code == 401
    assert bad_password_response.status_code == 401
    assert bad_email_response.json()["detail"] == bad_password_response.json()["detail"]
