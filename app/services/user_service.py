from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status
import uuid

from app.models.user import User, UserRole
from app.core.security import hash_password
from app.schemas.user import UserCreate, UserUpdate
from app.schemas.common import PaginatedResponse
from app.utils.utils import fullname



class UserService:
    @staticmethod
    async def create_user(
        payload: UserCreate, organization_id: uuid.UUID, db: AsyncSession
    ) -> User:
        if payload.role == UserRole.SUPERADMIN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Superdmin role cannot be assigned manually"
            )
            
        user_exists = await db.execute(select(User).where(User.email == payload.email))
        
        if user_exists.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists"
            )
            
        user = User(
            organization_id=organization_id,
            email=payload.email,
            full_name=fullname(payload.firstname, payload.lastname),
            hashed_password=hash_password(payload.password),
            role=payload.role,
            is_active=True
        )
        
        db.add(User)
        
        await db.commit()
        
        await db.refresh(user)
        
        return user
    
    
    @staticmethod
    async def list_users(
        db: AsyncSession, organization_id: uuid.UUID, 
        page: int = 1, per_page: int= 20
    ) -> PaginatedResponse:
        query = select(User).where(User.organization_id == organization_id)
        total = await db.scalar(select(func.count()).select_from(query.subquery()))
        result = await db.execute(query.order_by(User.created_at.desc()).offset((page-1) * per_page).limit(per_page))
        
        users = result.scalars().all()
        
        return PaginatedResponse(
            items=users,
            total=total,
            page=page,
            per_page=per_page,
            pages=-(-total // per_page)
        )