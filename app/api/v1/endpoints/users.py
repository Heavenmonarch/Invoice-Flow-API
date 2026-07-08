from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.core.database import get_db
from app.core.dependencies import get_current_active_staff, get_current_admin
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserOut
from app.schemas.common import PaginatedResponse
from app.services.user_service import UserService

router = APIRouter()


@router.post("/create-user", response_model=UserOut, status_code=201)
async def create_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    return await UserService.create_user(payload, current_user.organization_id, db)


@router.get("/list-users", response_model=PaginatedResponse[UserOut])
async def list_users(
    page: int = 1,
    per_page: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    return await UserService.list_users(db, current_user.organization_id, page, per_page)


@router.get("/my-profile", response_model=UserOut)
async def get_my_profile(
    current_user: User = Depends(get_current_active_staff),
):
    return current_user


@router.get("fetch-user/{user_id}", response_model=UserOut)
async def get_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    return await UserService.get_user(user_id, current_user.organization_id, db)


@router.patch("update-user/{user_id}", response_model=UserOut)
async def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    return await UserService.update_user(user_id, payload, current_user.organization_id, db)


@router.patch("/{user_id}/deactivate-user", response_model=UserOut)
async def deactivate_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    return await UserService.deactivate_user(user_id, current_user.organization_id, db)