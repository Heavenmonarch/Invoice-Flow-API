from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional

from app.models.commission import Commission, CommissionStatus
from app.models.user import User, UserRole
from app.core.exceptions import NotFoundException, BadRequestException
from app.schemas.commission import CommissionUpdate, CommissionSummary
from app.schemas.common import PaginatedResponse
from app.repositories.commission_repository import CommissionRepository
from app.utils.pagination import paginate


class CommissionService:

    @staticmethod
    async def list_commissions(
        db: AsyncSession,
        organization_id: UUID,
        staff_id: Optional[UUID] = None,
        period: Optional[str] = None,
        commission_status: Optional[CommissionStatus] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> PaginatedResponse:
        commission_repo = CommissionRepository(db)
        commissions, total = await commission_repo.list_by_org(
            organization_id, staff_id, period,
            commission_status, page, per_page,
        )
        return paginate(commissions, total, page, per_page)

    @staticmethod
    async def get_commission(
        commission_id: UUID,
        current_user: User,
        db: AsyncSession,
    ) -> Commission:
        commission_repo = CommissionRepository(db)
        commission = await commission_repo.get_by_id_and_org(
            commission_id, current_user.organization_id
        )

        if not commission:
            raise NotFoundException("Commission not found")

        if (
            current_user.role == UserRole.STAFF
            and commission.staff_id != current_user.id
        ):
            raise NotFoundException("Commission not found")

        return commission

    @staticmethod
    async def update_status(
        commission_id: UUID,
        payload: CommissionUpdate,
        organization_id: UUID,
        db: AsyncSession,
    ) -> Commission:
        commission_repo = CommissionRepository(db)
        commission = await commission_repo.get_by_id_and_org(
            commission_id, organization_id
        )

        if not commission:
            raise NotFoundException("Commission not found")

        invalid_transitions = {
            CommissionStatus.PAID: [
                CommissionStatus.PENDING,
                CommissionStatus.DISPUTED,
            ],
        }

        if commission.status in invalid_transitions.get(payload.status, []):
            raise BadRequestException(
                f"Cannot move commission from '{commission.status}' to '{payload.status}'"
            )

        commission.status = payload.status
        if payload.notes:
            commission.notes = payload.notes

        return await commission_repo.save(commission)

    @staticmethod
    async def get_summary(
        db: AsyncSession,
        organization_id: UUID,
        period: str,
    ) -> list[CommissionSummary]:
        commission_repo = CommissionRepository(db)
        return await commission_repo.get_summary_by_period(organization_id, period)