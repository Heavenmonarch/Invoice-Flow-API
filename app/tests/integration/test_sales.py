import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.product import Product


@pytest_asyncio.fixture
async def test_product(db: AsyncSession, test_org) -> Product:
    product = Product(
        organization_id=test_org.id,
        name="Test Product",
        price=100.00,
        commission_rate=10.0,
        is_active=True,
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


@pytest.mark.asyncio
async def test_submit_sale(
    client: AsyncClient, test_staff, test_product, staff_token
):
    response = await client.post(
        "/api/v1/submit-sale",
        json={
            "product_id": str(test_product.id),
            "quantity": 3,
        },
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["quantity"] == 3
    assert data["unit_price"] == 100.00
    assert data["total_amount"] == 300.00
    assert data["commission_rate"] == 10.0
    assert data["commission_amount"] == 30.00


@pytest.mark.asyncio
async def test_submit_sale_inactive_product_fails(
    client: AsyncClient, test_staff, test_product, staff_token, db
):
    test_product.is_active = False
    await db.commit()

    response = await client.post(
        "/api/v1/submit-sale",
        json={
            "product_id": str(test_product.id),
            "quantity": 1,
        },
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_staff_can_only_see_own_sales(
    client: AsyncClient, test_staff, staff_token
):
    response = await client.get(
        "/api/v1/sales/my-sales",
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    for sale in data["items"]:
        assert sale["staff_id"] == str(test_staff.id)


@pytest.mark.asyncio
async def test_admin_can_list_all_sales(
    client: AsyncClient, test_admin, admin_token
):
    response = await client.get(
        "/api/v1/list-sales",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200