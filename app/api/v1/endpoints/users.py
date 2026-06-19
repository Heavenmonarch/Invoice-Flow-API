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
    
    return user


@router.get("/list-users", response_model=PaginatedResponse[UserOut])
async def list_users (page: int = 1, per_page: int = 20, db: AsyncSession = Depends(get_db), current_user: User = get_current_admin):
    query = (
        select(User).where(User.organization_id == current_user.organization_id).where(User.is_active == True)
    )
    
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    results = await db.execute(query.offset((page - 1) * per_page).limit(per_page))
    users = results.scalars().all()
    
    return PaginatedResponse(
        items=users,
        total=total,
        page=page,
        per_page=per_page,
        pages=-(-total // per_page)
    )
    

@router.get("/fetch-user/{user_id}", response_model=UserOut)
async def get_user(user_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_admin)):
    
    result = await db.execute(select(User).where(User.id == user_id, User.organization_id == current_user.organization_id))
    
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@router.patch("/update-product/{user_id}", response_model=UserOut)
async def update_user(user_id: uuid.UUID, payload: UserUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_admin)):
    
    result = await db.execute(select(User).where(User.id == user_id, User.organization_id == current_user.organization_id))
    
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Product not found")
    
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
        
    await db.commit()
    await db.refresh(user)
    
    return user
