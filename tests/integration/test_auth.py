import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_organization(client: AsyncClient):
    response = await client.post("/api/v1/auth/register", json={
        "name": "Acme Corp",
        "email": "acme@test.com",
        "password": "Test@1234",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Acme Corp"
    assert data["email"] == "acme@test.com"
    assert "id" in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email_fails(client: AsyncClient):
    payload = {
        "name": "Duplicate Org",
        "email": "duplicate@test.com",
        "password": "Test@1234",
    }
    await client.post("/api/v1/auth/register", json=payload)
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_admin):
    response = await client.post("/api/v1/auth/login", json={
        "email": "admin@test.com",
        "password": "Test@1234",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, test_admin):
    response = await client.post("/api/v1/auth/login", json={
        "email": "admin@test.com",
        "password": "WrongPassword",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_email(client: AsyncClient):
    response = await client.post("/api/v1/auth/login", json={
        "email": "nobody@test.com",
        "password": "Test@1234",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient, test_admin):
    login = await client.post("/api/v1/auth/login", json={
        "email": "admin@test.com",
        "password": "Test@1234",
    })
    refresh_token = login.json()["refresh_token"]

    response = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": refresh_token,
    })
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_refresh_with_access_token_fails(client: AsyncClient, test_admin):
    login = await client.post("/api/v1/auth/login", json={
        "email": "admin@test.com",
        "password": "Test@1234",
    })
    access_token = login.json()["access_token"]
    response = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": access_token,
    })
    assert response.status_code == 401