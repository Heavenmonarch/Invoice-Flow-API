from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.schemas.organization import OrganizationCreate
from app.models.organization import Organization
import re


class AuthService:
    
    @classmethod
    def slugify(name: str) -> str:
        return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    
    @staticmethod
    async def register_user(payload: OrganizationCreate, db: AsyncSession):
        email_exists = await db.execute(select(Organization).where(Organization.email == payload.email))
        
        if email_exists.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
        
        # org = Organization(
        #     name=payload.name,
        #     slug=
        # )