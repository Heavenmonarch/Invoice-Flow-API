from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional

from app.models.target import Target, TargetType
from app.models.user import User, UserRole
from app.core.exceptions import (
    NotFoundException,
    ConflictException,
    BadRequestException,
    ForbiddenException,
)
from app.schemas.target import TargetCreate, TargetUpdate, TargetProgressOut
from app.schemas.common import PaginatedResponse
from app.repositories.target_repository import TargetRepository
from app.repositories.user_repository import UserRepository
from app.utils.pagination import paginate
from app.utils.audit import log_action


class TargetService:

    @staticmethod
    async def create_target(
        payload: TargetCreate,
        current_user: User,
        db: AsyncSession,
    ) -> Target:
        target_repo = TargetRepository(db)
        user_repo = UserRepository(db)

        # Verify staff member exists and belongs to same org
        staff = await user_repo.get_by_id_and_org(
            payload.staff_id, current_user.organization_id
        )
        if not staff:
            raise NotFoundException("Staff member not found")

        # Admins cannot set targets for other admins or superadmins
        if staff.role != UserRole.STAFF:
            raise BadRequestException(
                "Targets can only be set for staff members"
            )

        # Check for duplicate
        existing = await target_repo.get_by_staff_period_type(
            organization_id=current_user.organization_id,
            staff_id=payload.staff_id,
            period=payload.period,
            target_type=payload.target_type,
        )
        if existing:
            raise ConflictException(
                f"A {payload.target_type.value} target already exists "
                f"for this staff member for {payload.period}. "
                f"Update the existing target instead."
            )

        target = Target(
            organization_id=current_user.organization_id,
            staff_id=payload.staff_id,
            period=payload.period,
            target_type=payload.target_type,
            target_amount=payload.target_amount,
            notes=payload.notes,
        )
        target = await target_repo.create(target)

        await log_action(
            db=db,
            organization_id=current_user.organization_id,
            action="target.created",
            resource_type="target",
            actor=current_user,
            resource_id=target.id,
            metadata={
                "staff_id": str(payload.staff_id),
                "period": payload.period,
                "target_type": payload.target_type.value,
                "target_amount": payload.target_amount,
            },
        )

        await db.commit()
        await db.refresh(target)
        return target

    @staticmethod
    async def list_targets(
        db: AsyncSession,
        organization_id: UUID,
        period: Optional[str] = None,
        staff_id: Optional[UUID] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> PaginatedResponse:
        target_repo = TargetRepository(db)
        targets, total = await target_repo.list_by_org(
            organization_id, period, staff_id, page, per_page
        )
        return paginate(targets, total, page, per_page)

    @staticmethod
    async def get_target(
        target_id: UUID,
        organization_id: UUID,
        db: AsyncSession,
    ) -> Target:
        target_repo = TargetRepository(db)
        target = await target_repo.get_by_id_and_org(
            target_id, organization_id
        )
        if not target:
            raise NotFoundException("Target not found")
        return target

    @staticmethod
    async def update_target(
        target_id: UUID,
        payload: TargetUpdate,
        current_user: User,
        db: AsyncSession,
    ) -> Target:
        target_repo = TargetRepository(db)
        target = await target_repo.get_by_id_and_org(
            target_id, current_user.organization_id
        )
        if not target:
            raise NotFoundException("Target not found")

        updates = payload.model_dump(exclude_unset=True)
        old_values = {k: getattr(target, k) for k in updates}

        for field, value in updates.items():
            setattr(target, field, value)

        await log_action(
            db=db,
            organization_id=current_user.organization_id,
            action="target.updated",
            resource_type="target",
            actor=current_user,
            resource_id=target_id,
            metadata={
                "changes": updates,
                "previous": old_values,
            },
        )

        return await target_repo.save(target)

    @staticmethod
    async def get_progress(
        target_id: UUID,
        current_user: User,
        db: AsyncSession,
    ) -> TargetProgressOut:
      
        target_repo = TargetRepository(db)
        target = await target_repo.get_by_id_and_org(
            target_id, current_user.organization_id
        )
        if not target:
            raise NotFoundException("Target not found")

        # Staff can only see their own progress
        if (
            current_user.role == UserRole.STAFF
            and target.staff_id != current_user.id
        ):
            raise ForbiddenException("Access denied")

        current_amount = await target_repo.get_current_amount(
            organization_id=current_user.organization_id,
            staff_id=target.staff_id,
            period=target.period,
            target_type=target.target_type,
        )

        target_amount = float(target.target_amount)
        progress_percent = round(
            (current_amount / target_amount * 100) if target_amount > 0 else 0,
            2,
        )
        is_achieved = current_amount >= target_amount

        # Get staff name
        from app.repositories.user_repository import UserRepository
        user_repo = UserRepository(db)
        staff = await user_repo.get_by_id(target.staff_id)

        return TargetProgressOut(
            id=target.id,
            staff_id=target.staff_id,
            full_name=staff.full_name if staff else "Unknown",
            period=target.period,
            target_type=target.target_type,
            target_amount=target_amount,
            current_amount=current_amount,
            progress_percent=min(progress_percent, 100.0),
            is_achieved=is_achieved,
            notes=target.notes,
        )

    @staticmethod
    async def get_org_progress(
        organization_id: UUID,
        period: str,
        db: AsyncSession,
    ) -> list[TargetProgressOut]:

        target_repo = TargetRepository(db)
        targets = await target_repo.get_progress_by_org(
            organization_id, period
        )

        results = []
        for t in targets:
            current_amount = await target_repo.get_current_amount(
                organization_id=organization_id,
                staff_id=t["staff_id"],
                period=t["period"],
                target_type=t["target_type"],
            )
            target_amount = t["target_amount"]
            progress_percent = round(
                (current_amount / target_amount * 100)
                if target_amount > 0 else 0,
                2,
            )
            results.append(TargetProgressOut(
                id=t["id"],
                staff_id=t["staff_id"],
                full_name=t["full_name"],
                period=t["period"],
                target_type=t["target_type"],
                target_amount=target_amount,
                current_amount=current_amount,
                progress_percent=min(progress_percent, 100.0),
                is_achieved=current_amount >= target_amount,
                notes=t["notes"],
            ))

        return results

    @staticmethod
    async def get_my_progress(
        current_user: User,
        period: str,
        db: AsyncSession,
    ) -> list[TargetProgressOut]:
        target_repo = TargetRepository(db)
        targets_raw, _ = await target_repo.list_by_org(
            organization_id=current_user.organization_id,
            period=period,
            staff_id=current_user.id,
        )

        results = []
        for target in targets_raw:
            current_amount = await target_repo.get_current_amount(
                organization_id=current_user.organization_id,
                staff_id=current_user.id,
                period=period,
                target_type=target.target_type,
            )
            target_amount = float(target.target_amount)
            progress_percent = round(
                (current_amount / target_amount * 100)
                if target_amount > 0 else 0,
                2,
            )
            results.append(TargetProgressOut(
                id=target.id,
                staff_id=target.staff_id,
                full_name=current_user.full_name,
                period=period,
                target_type=target.target_type,
                target_amount=target_amount,
                current_amount=current_amount,
                progress_percent=min(progress_percent, 100.0),
                is_achieved=current_amount >= target_amount,
                notes=target.notes,
            ))

        return results