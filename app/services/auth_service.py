from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.schemas.organization import OrganizationCreate
from app.models.organization import Organization
from app.models.user import User, UserRole
from app.core.security import hash_password
from app.utils.utils import slugify



class AuthService:
    
    @classmethod
   
    
    @staticmethod
    async def register_user(payload: OrganizationCreate, db: AsyncSession):
        email_exists = await db.execute(select(Organization).where(Organization.email == payload.email))
        
        if email_exists.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
        
            
        org = Organization(
            name=payload.name,
            slug=slugify(payload.name),
            email=payload.email,
            is_active=True            
        )
        
        db.add(org)
        await db.flush()
        
        
        superadmin = User(
            organization_id = org.id,
            email=payload.email,
            full_name=payload.name,
            hashed_password=hash_password(payload.password),
            role=UserRole.SUPERADMIN,
            is_active=True
        )
        
        db.add(superadmin)
        
        await db.commit()
        
        await db.refresh(org)
        
        return org