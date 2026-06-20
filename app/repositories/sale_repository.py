from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
from datetime import datetime
from typing import Optional

from app.models.sale import Sale
from app.repositories.base_repository import BaseRepository


class SaleRepository(BaseRepository[Sale]):
    def __init__(self, db: AsyncSession):
        super().__init__(Sale, db)

    async def get_by_id_and_org(
        self,
        sale_id: UUID,
        organization_id: UUID,
    ) -> Sale | None:
        result = await self.db.execute(
            select(Sale).where(
                Sale.id == sale_id,
                Sale.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_org(
        self,
        organization_id: UUID,
        staff_id: Optional[UUID] = None,
        product_id: Optional[UUID] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Sale], int]:
        query = select(Sale).where(Sale.organization_id == organization_id)

        if staff_id:
            query = query.where(Sale.staff_id == staff_id)
        if product_id:
            query = query.where(Sale.product_id == product_id)
        if date_from:
            query = query.where(Sale.created_at >= date_from)
        if date_to:
            query = query.where(Sale.created_at <= date_to)

        total = await self.db.scalar(
            select(func.count()).select_from(query.subquery())
        )
        result = await self.db.execute(
            query.order_by(Sale.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        return result.scalars().all(), total

    async def total_revenue_by_org(self, organization_id: UUID) -> float:
        result = await self.db.scalar(
            select(func.sum(Sale.total_amount)).where(
                Sale.organization_id == organization_id
            )
        )
        return float(result or 0)

    async def count_by_org(self, organization_id: UUID) -> int:
        return await self.db.scalar(
            select(func.count(Sale.id)).where(
                Sale.organization_id == organization_id
            )
        )