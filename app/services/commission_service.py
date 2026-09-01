from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import Optional

from app.models.commission import Commission, CommissionStatus
from app.models.user import User, UserRole
from app.core.exceptions import NotFoundException, BadRequestException
from app.schemas.commission import CommissionUpdate, CommissionSummary
from app.schemas.common import PaginatedResponse
from app.repositories.commission_repository import CommissionRepository
from app.repositories.user_repository import UserRepository
from app.utils.pagination import paginate
from app.utils.audit import log_action
from app.utils.email import (
    send_commission_approved,
    send_commission_paid,
    send_commission_disputed,
    send_admin_commission_disputed,
)


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
        current_user: User,
        db: AsyncSession,
    ) -> Commission:
        commission_repo = CommissionRepository(db)
        user_repo = UserRepository(db)

        commission = await commission_repo.get_by_id_and_org(
            commission_id, current_user.organization_id
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
                f"Cannot move commission from '{commission.status}'"
                f" to '{payload.status}'"
            )

        old_status = commission.status
        commission.status = payload.status
        if payload.notes:
            commission.notes = payload.notes

        # Fetch the staff member for email
        staff = await user_repo.get_by_id(commission.staff_id)

        await log_action(
            db=db,
            organization_id=current_user.organization_id,
            action=f"commission.{payload.status.value}",
            resource_type="commission",
            actor=current_user,
            resource_id=commission_id,
            metadata={
                "old_status": old_status.value,
                "new_status": payload.status.value,
                "amount": float(commission.amount),
                "period": commission.period,
                "staff_id": str(commission.staff_id),
            },
        )

        result = await commission_repo.save(commission)

        # Send emails AFTER commit
        if staff:
            if payload.status == CommissionStatus.APPROVED:
                send_commission_approved(
                    to=staff.email,
                    full_name=staff.full_name,
                    amount=float(commission.amount),
                    period=commission.period,
                )
            elif payload.status == CommissionStatus.PAID:
                send_commission_paid(
                    to=staff.email,
                    full_name=staff.full_name,
                    amount=float(commission.amount),
                    period=commission.period,
                )
            elif payload.status == CommissionStatus.DISPUTED:
                send_commission_disputed(
                    to=staff.email,
                    full_name=staff.full_name,
                    amount=float(commission.amount),
                    period=commission.period,
                    notes=payload.notes,
                )
                # Also notify the admin who raised the dispute
                send_admin_commission_disputed(
                    to=current_user.email,
                    admin_name=current_user.full_name,
                    staff_name=staff.full_name,
                    amount=float(commission.amount),
                    period=commission.period,
                )

        return result

    @staticmethod
    async def get_summary(
        db: AsyncSession,
        organization_id: UUID,
        period: str,
    ) -> list[CommissionSummary]:
        commission_repo = CommissionRepository(db)
        return await commission_repo.get_summary_by_period(organization_id, period)