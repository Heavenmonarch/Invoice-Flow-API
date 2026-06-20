from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.organization import Organization
from app.repositories.base_repository import BaseRepository



class OrganizationRepository(BaseRepository[Organization]):
    def __init__(self, db: AsyncSession):
        super().__init__(Organization, db)
        
    async def get_by_email (self, email:str) -> Organization | None:
        result = await self.db.execute(
            select(Organization).where(Organization.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_by_slug(self, slug:str) -> Organization | None:
        result = await self.db.execute(
            select(Organization).where(Organization.slug == slug)
        )
        return result.scalar_one_or_none()
    
    async def slug_exists(self, slug: str) -> bool:
        result = await self.db.execute(
            select(Organization).where(Organization.slug == slug)
        )
        return result.scalar_one_or_none() is not None