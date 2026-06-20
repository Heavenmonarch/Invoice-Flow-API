from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
import re

from app.models.user import User, UserRole
from app.models.organization import Organization
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest
from app.schemas.organization import OrganizationCreate



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
    
    @staticmethod
    async def refresh(
        payload: RefreshRequest,
        db: AsyncSession
    ) -> TokenResponse:
        try:
            token_data = decode_token(payload.refresh_token)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e)
            )
            
        if token_data.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
            
        result = await db.execute(
            select(User).where(User.id == token_data["sub"])
        )
        
        user = result.scalar_one_or_none()
        
        if not user or user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        access_token= create_access_token(
            subject=user.id,
            extra_claims={
                "role": user.role.value,
                "org_id": str(user.organization_id)
            }
        )
        refresh_token = create_refresh_token(subject=user.id)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token
        )
        