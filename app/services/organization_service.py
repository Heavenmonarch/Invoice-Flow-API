from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.models.organization import Organization
from app.core.exceptions import NotFoundException
from app.schemas.organization import OrganizationUpdate
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.user_repository import UserRepository
from app.repositories.sale_repository import SaleRepository
from app.repositories.commission_repository import CommissionRepository


class OrganizationService:

    @staticmethod
    async def get_organization(
        organization_id: UUID,
        db: AsyncSession,
    ) -> Organization:
        org_repo = OrganizationRepository(db)
        org = await org_repo.get_by_id(organization_id)
        if not org:
            raise NotFoundException("Organization not found")
        return org

    @staticmethod
    async def update_organization(
        organization_id: UUID,
        payload: OrganizationUpdate,
        db: AsyncSession,
    ) -> Organization:
        org_repo = OrganizationRepository(db)
        org = await org_repo.get_by_id(organization_id)

        if not org:
            raise NotFoundException("Organization not found")

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(org, field, value)

        return await org_repo.save(org)

    @staticmethod
    async def get_stats(
        organization_id: UUID,
        db: AsyncSession,
    ) -> dict:
        user_repo = UserRepository(db)
        sale_repo = SaleRepository(db)
        commission_repo = CommissionRepository(db)

        total_staff = await user_repo.count_by_org(organization_id)
        total_sales = await sale_repo.count_by_org(organization_id)
        total_revenue = await sale_repo.total_revenue_by_org(organization_id)
        pending_commissions = await commission_repo.count_pending_by_org(organization_id)
        pending_commission_value = await commission_repo.sum_pending_by_org(organization_id)

        return {
            "total_staff": total_staff,
            "total_sales": total_sales,
            "total_revenue": total_revenue,
            "pending_commissions": pending_commissions,
            "pending_commission_value": pending_commission_value,
        }