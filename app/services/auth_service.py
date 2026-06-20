from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.schemas.organization import OrganizationCreate
from app.models.organization import Organization
from app.models.user import User, UserRole
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.utils.utils import slugify



class AuthService:
    
    @staticmethod
    async def register_organization(payload: OrganizationCreate, db: AsyncSession):
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
    
    
    
    @staticmethod
    async def login_user (payload: LoginRequest, db: AsyncSession):
        result = await db.execute(select(User).where(User.email == payload.email))
        user = result.scalar_one_or_none()
        
        if not user or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated"
            )
            
        access_token = create_access_token(
            subject=user.id,
            extra_claims={
                "role": user.role.value,
                "org_id": str(user.organization_id)
            }
        )
        
        refresh_token = create_refresh_token(subject=user.id)
        
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)
        