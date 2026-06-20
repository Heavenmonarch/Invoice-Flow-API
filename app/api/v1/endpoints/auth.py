from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.models.user import User, UserRole
from app.models.organization import Organization
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest
from app.schemas.organization import OrganizationCreate, OrganizationOut
from app.services.auth_service import AuthService
import re


router = APIRouter()


@router.post("/register", response_model=OrganizationOut, status_code=status.HTTP_201_CREATED)
async def register(payload: OrganizationCreate,db: AsyncSession = Depends(get_db)):
    return await AuthService.register_organization(payload, db)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await AuthService.login_user(payload, db)
    
    
@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        token_data = decode_token(payload.refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    
    if token_data.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    
    result = await db.execute(select(User).where(User.id == token_data["sub"]))
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user not found or inactive")
    
    access_token = create_access_token(
        subject=user.id,
        extra_claims={"role": user.role.value, "org_id": str(user.organization_id)}
    )
    
    refresh_token = create_refresh_token(subject=user.id)
    
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)