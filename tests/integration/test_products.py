import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_product(client: AsyncClient, test_admin, admin_token):
    response = await client.post(
        "/api/v1/products/create-product",
        json={
            "name": "Widget Pro",
            "description": "A great widget",
            "category": "Electronics",
            "price": 199.99,
            "commission_rate": 7.5,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Widget Pro"
    assert data["price"] == 199.99
    assert data["commission_rate"] == 7.5
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_staff_cannot_create_product(
    client: AsyncClient, test_staff, staff_token
):
    response = await client.post(
        "/api/v1/products/create-product",
        json={
            "name": "Unauthorized Product",
            "price": 50.00,
            "commission_rate": 5.0,
        },
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_products(client: AsyncClient, test_staff, staff_token):
    response = await client.get(
        "/api/v1/products/list-products",
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_create_product_negative_price_fails(
    client: AsyncClient, admin_token
):
    response = await client.post(
        "/api/v1/products/create-product",
        json={
            "name": "Bad Product",
            "price": -10.00,
            "commission_rate": 5.0,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_product_invalid_commission_rate_fails(
    client: AsyncClient, admin_token
):
    response = await client.post(
        "/api/v1/products/create-product",
        json={
            "name": "Bad Commission",
            "price": 100.00,
            "commission_rate": 150.0, 
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 422