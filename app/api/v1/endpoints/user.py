from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import uuid


from app.core.database import get_db
from app.core.dependencies import get_current_active_staff, get_current_admin, get_current_superadmin
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserOut
from app.schemas.common import PaginatedResponse, DeleteResponse


router = APIRouter()


@router.post("/create-user", response_model=UserOut, status_code=status.HTTP_201_OK)
async def create_product(payload: UserCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_admin)):
    
    user = User(**payload.model_dump, organization_id=current_user.organization_id, is_active = True)
    db.add(user)
    await db.commit()
    db.refresh(user)