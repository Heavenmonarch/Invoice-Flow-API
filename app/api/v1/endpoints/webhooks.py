from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.models.user import User
from app.schemas.webhook import (
    WebhookCreate,
    WebhookUpdate,
    WebhookOut,
    WebhookDeliveryOut,
    WebhookSecretOut,
)
from app.schemas.common import PaginatedResponse
from app.services.webhook_service import WebhookService

router = APIRouter()


@router.post("", response_model=WebhookSecretOut, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    payload: WebhookCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Register a new webhook URL.
    Returns the webhook secret ONCE — store it immediately.
    It cannot be retrieved again.
    """
    webhook, plain_secret = await WebhookService.create_webhook(
        payload, current_user, db
    )
    return WebhookSecretOut(id=webhook.id, secret=plain_secret)


@router.get("", response_model=PaginatedResponse[WebhookOut])
async def list_webhooks(
    page: int = 1,
    per_page: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    return await WebhookService.list_webhooks(
        current_user.organization_id, db, page, per_page
    )


@router.get("/{webhook_id}", response_model=WebhookOut)
async def get_webhook(
    webhook_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    return await WebhookService.get_webhook(
        webhook_id, current_user.organization_id, db
    )


@router.patch("/{webhook_id}", response_model=WebhookOut)
async def update_webhook(
    webhook_id: UUID,
    payload: WebhookUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    return await WebhookService.update_webhook(
        webhook_id, payload, current_user, db
    )


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    await WebhookService.delete_webhook(webhook_id, current_user, db)


@router.get("/{webhook_id}/deliveries", response_model=PaginatedResponse[WebhookDeliveryOut])
async def list_deliveries(
    webhook_id: UUID,
    page: int = 1,
    per_page: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Returns the delivery history for a webhook.
    Shows payload, response status, and success/failure per attempt.
    Use this to debug why a webhook integration isn't receiving events.
    """
    return await WebhookService.list_deliveries(
        webhook_id, current_user.organization_id, db, page, per_page
    )