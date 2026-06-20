from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import uuid

from app.core.database import get_db
from app.core.dependencies import get_current_active_staff, get_current_admin
from app.models.user import User
from app.models.commission import CommissionStatus
from app.schemas.commission import CommissionUpdate, CommissionOut, CommissionSummary
from app.schemas.common import PaginatedResponse
from app.services.commission_service import CommissionService

router = APIRouter()


@router.get("/list-commissions", response_model=PaginatedResponse[CommissionOut])
async def list_commissions(
    page: int = 1,
    per_page: int = 20,
    staff_id: Optional[uuid.UUID] = None,
    period: Optional[str] = None,
    commission_status: Optional[CommissionStatus] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    return await CommissionService.list_commissions(
        db, current_user.organization_id,
        staff_id, period, commission_status,
        page, per_page,
    )


@router.get("/my-commissions", response_model=PaginatedResponse[CommissionOut])
async def my_commissions(
    page: int = 1,
    per_page: int = 20,
    period: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_staff),
):
    return await CommissionService.list_commissions(
        db, current_user.organization_id,
        staff_id=current_user.id,
        period=period,
        page=page,
        per_page=per_page,
    )


@router.get("/get-commission-summary", response_model=List[CommissionSummary])
async def commission_summary(
    period: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    return await CommissionService.get_summary(
        db, current_user.organization_id, period
    )


@router.get("fetch-commission/{commission_id}", response_model=CommissionOut)
async def get_commission(
    commission_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_staff),
):
    return await CommissionService.get_commission(
        commission_id, current_user, db
    )


@router.patch("update-commission/{commission_id}", response_model=CommissionOut)
async def update_commission_status(
    commission_id: uuid.UUID,
    payload: CommissionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    return await CommissionService.update_status(
        commission_id, payload, current_user.organization_id, db
    )