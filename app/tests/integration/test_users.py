import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_user_as_admin(
    client: AsyncClient, test_org, test_admin, admin_token
):
    response = await client.post(
        "/api/v1/users/create-user",
        json={
            "email": "newstaff@test.com",
            "full_name": "New Staff",
            "password": "Test@1234",
            "role": "staff",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newstaff@test.com"
    assert data["role"] == "staff"
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_create_superadmin_role_fails(
    client: AsyncClient, admin_token
):
    response = await client.post(
        "/api/v1/users/create-user",
        json={
            "email": "fake_super@test.com",
            "full_name": "Fake Super",
            "password": "Test@1234",
            "role": "superadmin",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_staff_cannot_create_user(
    client: AsyncClient, test_staff, staff_token
):
    response = await client.post(
        "/api/v1/users/create-user",
        json={
            "email": "another@test.com",
            "full_name": "Another",
            "password": "Test@1234",
            "role": "staff",
        },
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_users(client: AsyncClient, test_admin, admin_token):
    response = await client.get(
        "/api/v1/users/list-users",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, test_staff, staff_token):
    response = await client.get(
        "/api/v1/users/my-profile",
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == "staff@test.com"


@pytest.mark.asyncio
async def test_deactivate_user(
    client: AsyncClient, test_staff, admin_token
):
    response = await client.patch(
        f"/users/{test_staff.id}/deactivate-user",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is False