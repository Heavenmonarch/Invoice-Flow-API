import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.product import Product


@pytest.mark.asyncio
async def test_commission_created_on_sale(
    client: AsyncClient, test_staff, test_product, staff_token, admin_token
):
    # when we submit a sale
    await client.post(
        "/api/v1/sales/submit-sale",
        json={"product_id": str(test_product.id), "quantity": 2},
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    
    # when admin checks the commission after the sale has been submitted
    response = await client.get(
        "/api/v1/commissions/list-commissions",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1

    # commission should be pending
    commission = data["items"][0]
    assert commission["status"] == "pending"


@pytest.mark.asyncio
async def test_admin_can_approve_commission(
    client: AsyncClient, test_staff, test_product, staff_token, admin_token
):
    # a new sale is created, so that the commission for that sale can exist in this instance
    await client.post(
        "/api/v1/sales/submit-sales",
        json={"product_id": str(test_product.id), "quantity": 1},
        headers={"Authorization": f"Bearer {staff_token}"},
    )

    # list the commissions
    commissions = await client.get(
        "/api/v1/commissions/list-commissions",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    commission_id = commissions.json()["items"][0]["id"]

    # Approve the commission
    response = await client.patch(
        f"/api/v1/commissions/{commission_id}",
        json={"status": "approved"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "approved"


@pytest.mark.asyncio
async def test_cannot_skip_to_paid_from_pending(
    client: AsyncClient, test_staff, test_product, staff_token, admin_token
):
    await client.post(
        "/api/v1/sales/submit-sale",
        json={"product_id": str(test_product.id), "quantity": 1},
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    commissions = await client.get(
        "/api/v1/commissions/list-commissions",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    commission_id = commissions.json()["items"][0]["id"]

    # Try to mark paid while still pending will fail
    response = await client.patch(
        f"/api/v1/commissions/update-commission/{commission_id}",
        json={"status": "paid"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_staff_can_only_see_own_commissions(
    client: AsyncClient, test_staff, staff_token
):
    response = await client.get(
        "/api/v1/commissions/my-commissions",
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert response.status_code == 200
    for commission in response.json()["items"]:
        assert commission["staff_id"] == str(test_staff.id)