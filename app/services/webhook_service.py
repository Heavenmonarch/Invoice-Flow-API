import secrets
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional

from app.models.webhook import Webhook
from app.models.user import User
from app.core.exceptions import (
    NotFoundException,
    BadRequestException,
    ForbiddenException,
)
from app.schemas.webhook import WebhookCreate, WebhookUpdate, WEBHOOK_EVENTS
from app.schemas.common import PaginatedResponse
from app.repositories.webhook_repository import WebhookRepository
from app.utils.pagination import paginate
from app.utils.audit import log_action
from app.utils.webhook import build_payload, deliver_webhook

logger = logging.getLogger(__name__)


class WebhookService:

    @staticmethod
    async def create_webhook(
        payload: WebhookCreate,
        current_user: User,
        db: AsyncSession,
    ) -> tuple[Webhook, str]:
        """
        Returns (webhook, plain_secret).
        The plain secret is shown once and never stored — only
        the hashed version lives in the database.
        """
        # Validate events
        invalid = set(payload.events) - WEBHOOK_EVENTS
        if invalid:
            raise BadRequestException(
                f"Invalid event types: {', '.join(invalid)}. "
                f"Valid events: {', '.join(sorted(WEBHOOK_EVENTS))}"
            )

        if not payload.events:
            raise BadRequestException(
                "At least one event must be specified"
            )

        # Generate a cryptographically secure secret
        plain_secret = secrets.token_hex(32)

        webhook_repo = WebhookRepository(db)
        webhook = Webhook(
            organization_id=current_user.organization_id,
            url=str(payload.url),
            secret=plain_secret,
            events=payload.events,
            description=payload.description,
            is_active=True,
        )
        webhook = await webhook_repo.create(webhook)

        await log_action(
            db=db,
            organization_id=current_user.organization_id,
            action="webhook.created",
            resource_type="webhook",
            actor=current_user,
            resource_id=webhook.id,
            metadata={
                "url": str(payload.url),
                "events": payload.events,
            },
        )

        await db.commit()
        await db.refresh(webhook)
        return webhook, plain_secret

    @staticmethod
    async def list_webhooks(
        organization_id: UUID,
        db: AsyncSession,
        page: int = 1,
        per_page: int = 20,
    ) -> PaginatedResponse:
        webhook_repo = WebhookRepository(db)
        webhooks, total = await webhook_repo.list_by_org(
            organization_id, page, per_page
        )
        return paginate(webhooks, total, page, per_page)

    @staticmethod
    async def get_webhook(
        webhook_id: UUID,
        organization_id: UUID,
        db: AsyncSession,
    ) -> Webhook:
        webhook_repo = WebhookRepository(db)
        webhook = await webhook_repo.get_by_id_and_org(
            webhook_id, organization_id
        )
        if not webhook:
            raise NotFoundException("Webhook not found")
        return webhook

    @staticmethod
    async def update_webhook(
        webhook_id: UUID,
        payload: WebhookUpdate,
        current_user: User,
        db: AsyncSession,
    ) -> Webhook:
        webhook_repo = WebhookRepository(db)
        webhook = await webhook_repo.get_by_id_and_org(
            webhook_id, current_user.organization_id
        )
        if not webhook:
            raise NotFoundException("Webhook not found")

        updates = payload.model_dump(exclude_unset=True)

        if "events" in updates:
            invalid = set(updates["events"]) - WEBHOOK_EVENTS
            if invalid:
                raise BadRequestException(
                    f"Invalid event types: {', '.join(invalid)}"
                )
            if not updates["events"]:
                raise BadRequestException(
                    "At least one event must be specified"
                )

        if "url" in updates:
            updates["url"] = str(updates["url"])

        for field, value in updates.items():
            setattr(webhook, field, value)

        await log_action(
            db=db,
            organization_id=current_user.organization_id,
            action="webhook.updated",
            resource_type="webhook",
            actor=current_user,
            resource_id=webhook_id,
            metadata=updates,
        )

        return await webhook_repo.save(webhook)

    @staticmethod
    async def delete_webhook(
        webhook_id: UUID,
        current_user: User,
        db: AsyncSession,
    ) -> None:
        webhook_repo = WebhookRepository(db)
        webhook = await webhook_repo.get_by_id_and_org(
            webhook_id, current_user.organization_id
        )
        if not webhook:
            raise NotFoundException("Webhook not found")

        await log_action(
            db=db,
            organization_id=current_user.organization_id,
            action="webhook.deleted",
            resource_type="webhook",
            actor=current_user,
            resource_id=webhook_id,
            metadata={"url": webhook.url},
        )

        await webhook_repo.delete(webhook)

    @staticmethod
    async def list_deliveries(
        webhook_id: UUID,
        organization_id: UUID,
        db: AsyncSession,
        page: int = 1,
        per_page: int = 20,
    ) -> PaginatedResponse:
        webhook_repo = WebhookRepository(db)

        # Verify webhook belongs to org
        webhook = await webhook_repo.get_by_id_and_org(
            webhook_id, organization_id
        )
        if not webhook:
            raise NotFoundException("Webhook not found")

        deliveries, total = await webhook_repo.list_deliveries(
            webhook_id, page, per_page
        )
        return paginate(deliveries, total, page, per_page)

    @staticmethod
    async def dispatch_event(
        event: str,
        data: dict,
        organization_id: UUID,
        db: AsyncSession,
    ) -> None:
        """
        Finds all active webhooks subscribed to this event
        and delivers the payload to each one.
        Called internally by other services after their
        primary operation succeeds.
        Delivery failures are logged but never raise exceptions —
        a failed webhook must never break the main operation.
        """
        webhook_repo = WebhookRepository(db)
        webhooks = await webhook_repo.get_active_by_event(
            organization_id, event
        )

        if not webhooks:
            return

        payload = build_payload(event, data, organization_id)

        for webhook in webhooks:
            try:
                success, status_code, response_body = await deliver_webhook(
                    url=webhook.url,
                    secret=webhook.secret,
                    event=event,
                    payload=payload,
                )

                await webhook_repo.log_delivery(
                    webhook_id=webhook.id,
                    event=event,
                    payload=payload,
                    response_status=status_code,
                    response_body=response_body,
                    success=success,
                    attempt=1,
                )
                await db.commit()

            except Exception as e:
                logger.error(
                    "Webhook dispatch error | event=%s | webhook=%s | error=%s",
                    event, webhook.id, str(e),
                )