from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
from typing import Optional

from app.models.webhook import Webhook, WebhookDelivery
from app.repositories.base_repository import BaseRepository


class WebhookRepository(BaseRepository[Webhook]):
    def __init__(self, db: AsyncSession):
        super().__init__(Webhook, db)

    async def get_by_id_and_org(
        self,
        webhook_id: UUID,
        organization_id: UUID,
    ) -> Webhook | None:
        result = await self.db.execute(
            select(Webhook).where(
                Webhook.id == webhook_id,
                Webhook.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_org(
        self,
        organization_id: UUID,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Webhook], int]:
        query = select(Webhook).where(
            Webhook.organization_id == organization_id
        )
        total = await self.db.scalar(
            select(func.count()).select_from(query.subquery())
        )
        result = await self.db.execute(
            query.order_by(Webhook.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        return result.scalars().all(), total

    async def get_active_by_event(
        self,
        organization_id: UUID,
        event: str,
    ) -> list[Webhook]:
        """
        Returns all active webhooks for an org that are
        subscribed to a specific event.
        Used by the dispatcher to find which URLs to call.
        """
        result = await self.db.execute(
            select(Webhook).where(
                Webhook.organization_id == organization_id,
                Webhook.is_active == True,
            )
        )
        webhooks = result.scalars().all()
        # Filter in Python — JSON array containment in Postgres
        # requires dialect-specific syntax; this is simpler and
        # the number of webhooks per org is always small
        return [w for w in webhooks if event in w.events]

    async def log_delivery(
        self,
        webhook_id: UUID,
        event: str,
        payload: dict,
        response_status: Optional[int],
        response_body: Optional[str],
        success: bool,
        attempt: int,
    ) -> WebhookDelivery:
        delivery = WebhookDelivery(
            webhook_id=webhook_id,
            event=event,
            payload=payload,
            response_status=response_status,
            response_body=response_body,
            success=success,
            attempt=attempt,
        )
        self.db.add(delivery)
        await self.db.flush()
        return delivery

    async def list_deliveries(
        self,
        webhook_id: UUID,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[WebhookDelivery], int]:
        query = select(WebhookDelivery).where(
            WebhookDelivery.webhook_id == webhook_id
        )
        total = await self.db.scalar(
            select(func.count()).select_from(query.subquery())
        )
        result = await self.db.execute(
            query.order_by(WebhookDelivery.delivered_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        return result.scalars().all(), total