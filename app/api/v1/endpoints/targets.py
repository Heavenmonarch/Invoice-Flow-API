from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import uuid

from app.core.database import get_db
from app.core.dependencies import get_current_active_staff, get_current_admin
from app.models.user import User
from app.schemas.target import TargetCreate, TargetUpdate, TargetOut, TargetProgressOut
from app.schemas.common import PaginatedResponse
from app.services.target_service import TargetService

router = APIRouter()


@router.post("", response_model=TargetOut, status_code=201)
async def create_target(
    payload: TargetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    return await TargetService.create_target(payload, current_user, db)


@router.get("", response_model=PaginatedResponse[TargetOut])
async def list_targets(
    page: int = 1,
    per_page: int = 20,
    period: Optional[str] = Query(None, description="Filter by period e.g. 2025-06"),
    staff_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    return await TargetService.list_targets(
        db, current_user.organization_id, period, staff_id, page, per_page
    )


@router.get("/progress", response_model=List[TargetProgressOut])
async def org_progress(
    period: str = Query(..., description="Period in YYYY-MM format"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    return await TargetService.get_org_progress(
        current_user.organization_id, period, db
    )


@router.get("/mine", response_model=List[TargetProgressOut])
async def my_progress(
    period: str = Query(..., description="Period in YYYY-MM format"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_staff),
):
    return await TargetService.get_my_progress(current_user, period, db)


@router.get("/{target_id}", response_model=TargetProgressOut)
async def get_target_progress(
    target_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_staff),
):
    """Get a single target with live progress data."""
    return await TargetService.get_progress(target_id, current_user, db)


@router.patch("/{target_id}", response_model=TargetOut)
async def update_target(
    target_id: uuid.UUID,
    payload: TargetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Update a target amount or notes. Period and type cannot be changed."""
    return await TargetService.update_target(
        target_id, payload, current_user, db
    )