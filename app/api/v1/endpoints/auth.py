from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.models.user import User, UserRole
from app.models.organization import Organization
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest
from app.schemas.organization import OrganizationCreate, OrganizationOut
import re


router = APIRouter()


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


@router.post("/register", response_model=OrganizationOut, status_code=status.HTTP_201_CREATED)
async def register(payload: OrganizationCreate,db: AsyncSession = Depends(get_db)):
    email_exists =  await db.execute(select(Organization).where(Organization.email == payload.email))
    if email_exists.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")
    
    
    org = Organization(
        name=payload.name,
        slug=slugify(payload.name),
        email=payload.email,
        is_active=True
    )
    
    db.add(org)
    await db.flush()
    
    superadmin = User(
        organization_id=org.id,
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