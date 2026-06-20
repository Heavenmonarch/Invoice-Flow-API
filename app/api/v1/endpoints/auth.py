from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest
from app.schemas.organization import OrganizationCreate, OrganizationOut
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register-organization", response_model=OrganizationOut, status_code=201)
async def register(
    payload: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
):
    return await AuthService.register(payload, db)


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    return await AuthService.login(payload, db)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    return await AuthService.refresh(payload, db)