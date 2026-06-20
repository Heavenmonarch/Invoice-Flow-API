from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status
import uuid

from app.models.organization import Organization
from app.models.user import User
from app.models.sale import Sale
from app.models.commission import Commission, CommissionStatus
from app.schemas.organization import OrganizationUpdate


class OrganizationService:

    @staticmethod
    async def get_organization(
        organization_id: uuid.UUID,
        db: AsyncSession,
    ) -> Organization:
        result = await db.execute(
            select(Organization).where(Organization.id == organization_id)
        )
        org = result.scalar_one_or_none()
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )
        return org

    @staticmethod
    async def update_organization(
        organization_id: uuid.UUID,
        payload: OrganizationUpdate,
        db: AsyncSession,
    ) -> Organization:
        org = await OrganizationService.get_organization(organization_id, db)

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(org, field, value)

        await db.commit()
        await db.refresh(org)
        return org

    @staticmethod
    async def get_stats(
        organization_id: uuid.UUID,
        db: AsyncSession,
    ) -> dict:
        total_staff = await db.scalar(
            select(func.count(User.id)).where(
                User.organization_id == organization_id,
                User.is_active == True,
            )
        )
        total_sales = await db.scalar(
            select(func.count(Sale.id)).where(
                Sale.organization_id == organization_id
            )
        )
        total_revenue = await db.scalar(
            select(func.sum(Sale.total_amount)).where(
                Sale.organization_id == organization_id
            )
        ) or 0

        pending_commissions = await db.scalar(
            select(func.count(Commission.id)).where(
                Commission.organization_id == organization_id,
                Commission.status == CommissionStatus.PENDING,
            )
        )
        pending_commission_value = await db.scalar(
            select(func.sum(Commission.amount)).where(
                Commission.organization_id == organization_id,
                Commission.status == CommissionStatus.PENDING,
            )
        ) or 0

        return {
            "total_staff": total_staff,
            "total_sales": total_sales,
            "total_revenue": float(total_revenue),
            "pending_commissions": pending_commissions,
            "pending_commission_value": float(pending_commission_value),
        }