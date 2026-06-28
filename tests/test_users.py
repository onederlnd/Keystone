# tests/test_users.py

import pytest


@pytest.mark.asyncio
async def test_get_me(client, auth_headers):
    headers = await auth_headers()
    response = await client.get("/users/me", headers=headers)
    assert response.status_code == 200
    assert "email" in response.json()


@pytest.mark.asyncio
async def test_get_user(client, auth_headers, create_user_in_db):
    user = await create_user_in_db(email="target@test.com")
    headers = await auth_headers()
    response = await client.get(f"/users/{user.id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "target@test.com"


@pytest.mark.asyncio
async def test_get_user_not_found(client, auth_headers):
    headers = await auth_headers()
    response = await client.get(
        "/users/00000000-0000-0000-0000-000000000000", headers=headers
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_patch_user_self(client, auth_headers, create_user_in_db):
    from app.models.user import UserRole

    user = await create_user_in_db(email="edit@test.com", role=UserRole.buyer)
    token = __import__(
        "app.core.security", fromlist=["create_access_token"]
    ).create_access_token({"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.patch(
        f"/users/{user.id}", json={"full_name": "Updated"}, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated"


@pytest.mark.asyncio
async def test_delete_user_admin_only(client, auth_headers, create_user_in_db):
    from app.models.user import UserRole

    target = await create_user_in_db(email="target2@test.com")

    # non-admin should get 403
    headers = await auth_headers(role=UserRole.buyer)
    response = await client.delete(f"/users/{target.id}", headers=headers)
    assert response.status_code == 403

    # admin should succeed
    headers = await auth_headers(role=UserRole.admin)
    response = await client.delete(f"/users/{target.id}", headers=headers)
    assert response.status_code == 204
