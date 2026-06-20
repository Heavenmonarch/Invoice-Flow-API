from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
from typing import Optional

from app.models.commission import Commission, CommissionStatus
from app.models.user import User
from app.repositories.base_repository import BaseRepository
from app.schemas.commission import CommissionSummary


class CommissionRepository(BaseRepository[Commission]):
    def __init__(self, db: AsyncSession):
        super().__init__(Commission, db)

    async def get_by_id_and_org(
        self,
        commission_id: UUID,
        organization_id: UUID,
    ) -> Commission | None:
        result = await self.db.execute(
            select(Commission).where(
                Commission.id == commission_id,
                Commission.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_org(
        self,
        organization_id: UUID,
        staff_id: Optional[UUID] = None,
        period: Optional[str] = None,
        commission_status: Optional[CommissionStatus] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Commission], int]:
        query = select(Commission).where(
            Commission.organization_id == organization_id
        )

        if staff_id:
            query = query.where(Commission.staff_id == staff_id)
        if period:
            query = query.where(Commission.period == period)
        if commission_status:
            query = query.where(Commission.status == commission_status)

        total = await self.db.scalar(
            select(func.count()).select_from(query.subquery())
        )
        result = await self.db.execute(
            query.order_by(Commission.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        return result.scalars().all(), total

    async def get_summary_by_period(
        self,
        organization_id: UUID,
        period: str,
    ) -> list[CommissionSummary]:
        result = await self.db.execute(
            select(
                Commission.staff_id,
                User.full_name,
                Commission.period,
                func.count(Commission.id).label("total_sales"),
                func.sum(Commission.amount).label("total_commission"),
                Commission.status,
            )
            .join(User, User.id == Commission.staff_id)
            .where(
                Commission.organization_id == organization_id,
                Commission.period == period,
            )
            .group_by(
                Commission.staff_id,
                User.full_name,
                Commission.period,
                Commission.status,
            )
        )
        rows = result.all()
        return [
            CommissionSummary(
                staff_id=row.staff_id,
                full_name=row.full_name,
                period=row.period,
                total_sales=row.total_sales,
                total_amount=0,
                total_commission=float(row.total_commission),
                status=row.status,
            )
            for row in rows
        ]

    async def count_pending_by_org(self, organization_id: UUID) -> int:
        return await self.db.scalar(
            select(func.count(Commission.id)).where(
                Commission.organization_id == organization_id,
                Commission.status == CommissionStatus.PENDING,
            )
        )

    async def sum_pending_by_org(self, organization_id: UUID) -> float:
        result = await self.db.scalar(
            select(func.sum(Commission.amount)).where(
                Commission.organization_id == organization_id,
                Commission.status == CommissionStatus.PENDING,
            )
        )
        return float(result or 0)