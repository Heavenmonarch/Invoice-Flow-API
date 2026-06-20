from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_admin, get_current_superadmin
from app.models.user import User
from app.schemas.organization import OrganizationOut, OrganizationUpdate
from app.services.organization_service import OrganizationService

router = APIRouter()


@router.get("/fetch-organization", response_model=OrganizationOut)
async def get_organization(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    return await OrganizationService.get_organization(current_user.organization_id, db)


@router.patch("/update-organization", response_model=OrganizationOut)
async def update_organization(
    payload: OrganizationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superadmin),
):
    return await OrganizationService.update_organization(
        current_user.organization_id, payload, db
    )


@router.get("/organization-stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    return await OrganizationService.get_stats(current_user.organization_id, db)