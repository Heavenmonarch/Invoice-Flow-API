import uuid
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime


# All supported webhook event types
WEBHOOK_EVENTS = {
    "sale.created",
    "commission.approved",
    "commission.paid",
    "commission.disputed",
    "user.invited",
    "user.deactivated",
}


class WebhookCreate(BaseModel):
    url: HttpUrl
    events: List[str]
    description: Optional[str] = None

    def validate_events(self):
        invalid = set(self.events) - WEBHOOK_EVENTS
        if invalid:
            raise ValueError(
                f"Invalid events: {invalid}. "
                f"Valid events are: {WEBHOOK_EVENTS}"
            )


class WebhookUpdate(BaseModel):
    url: Optional[HttpUrl] = None
    events: Optional[List[str]] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class WebhookOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    url: str
    events: List[str]
    description: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class WebhookDeliveryOut(BaseModel):
    id: uuid.UUID
    webhook_id: uuid.UUID
    event: str
    payload: dict
    response_status: Optional[int]
    response_body: Optional[str]
    success: bool
    attempt: int
    delivered_at: datetime

    model_config = {"from_attributes": True}


class WebhookSecretOut(BaseModel):
    """
    Returned only at creation time.
    The secret is never exposed again after this —
    the admin must store it immediately.
    """
    id: uuid.UUID
    secret: str
    message: str = (
        "Store this secret securely. "
        "It will not be shown again. "
        "Use it to verify webhook signatures on your server."
    )