from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Generic, TypeVar, Type
from uuid import UUID

from app.core.database import Base


ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db
        
    async def get_by_id(self, id: UUID) -> ModelType | None:
        result = await self.db.execute(
            select(self.model).where(self.model.id ==  id)
        )
        
        return result.scalar_one_or_none()
    
    async def get_all(self, page: int =1, per_page: int = 20) -> tuple[list[ModelType], int]:
        
        query = select(self.model)
        total = await self.db.scalar(
            select(func.count()).select_from(query.subquery())
        )
        result = await self.db.execute(
            query.offset((page-1) * per_page).limit(per_page)
        )
        return result.scalars().all(), total
    
    async def create(self, instance: ModelType) -> ModelType:
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance
    
    
    async def save(self, instance: ModelType) -> ModelType:
        await self.db.commit()
        await self.db.refresh(instance)
        return instance
    
    async def delete(self, instance: ModelType):
        await self.db.delete(instance)
        await self.db.commit()
        