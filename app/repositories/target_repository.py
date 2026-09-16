from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
from typing import Optional

from app.models.target import Target, TargetType
from app.models.sale import Sale
from app.models.commission import Commission
from app.models.user import User
from app.repositories.base_repository import BaseRepository


class TargetRepository(BaseRepository[Target]):
    def __init__(self, db: AsyncSession):
        super().__init__(Target, db)

    async def get_by_id_and_org(
        self,
        target_id: UUID,
        organization_id: UUID,
    ) -> Target | None:
        result = await self.db.execute(
            select(Target).where(
                Target.id == target_id,
                Target.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_staff_period_type(
        self,
        organization_id: UUID,
        staff_id: UUID,
        period: str,
        target_type: TargetType,
    ) -> Target | None:
    
        result = await self.db.execute(
            select(Target).where(
                Target.organization_id == organization_id,
                Target.staff_id == staff_id,
                Target.period == period,
                Target.target_type == target_type,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_org(
        self,
        organization_id: UUID,
        period: Optional[str] = None,
        staff_id: Optional[UUID] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Target], int]:
        query = select(Target).where(
            Target.organization_id == organization_id
        )
        if period:
            query = query.where(Target.period == period)
        if staff_id:
            query = query.where(Target.staff_id == staff_id)

        total = await self.db.scalar(
            select(func.count()).select_from(query.subquery())
        )
        result = await self.db.execute(
            query.order_by(Target.period.desc(), Target.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        return result.scalars().all(), total

    async def get_current_amount(
        self,
        organization_id: UUID,
        staff_id: UUID,
        period: str,
        target_type: TargetType,
    ) -> float:
  
        if target_type == TargetType.REVENUE:
            result = await self.db.scalar(
                select(func.sum(Sale.total_amount)).where(
                    Sale.organization_id == organization_id,
                    Sale.staff_id == staff_id,
                    Sale.created_at.cast(
                        __import__('sqlalchemy').String
                    ).like(f"{period}%"),
                )
            )
        else:
            result = await self.db.scalar(
                select(func.sum(Commission.amount)).where(
                    Commission.organization_id == organization_id,
                    Commission.staff_id == staff_id,
                    Commission.period == period,
                )
            )
        return float(result or 0)

    async def get_progress_by_org(
        self,
        organization_id: UUID,
        period: str,
    ) -> list[dict]:
  
        result = await self.db.execute(
            select(
                Target.id,
                Target.staff_id,
                User.full_name,
                Target.period,
                Target.target_type,
                Target.target_amount,
                Target.notes,
            )
            .join(User, User.id == Target.staff_id)
            .where(
                Target.organization_id == organization_id,
                Target.period == period,
            )
            .order_by(User.full_name)
        )
        return [
            {
                "id": row.id,
                "staff_id": row.staff_id,
                "full_name": row.full_name,
                "period": row.period,
                "target_type": row.target_type,
                "target_amount": float(row.target_amount),
                "notes": row.notes,
            }
            for row in result.all()
        ]