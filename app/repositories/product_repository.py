from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
from typing import Optional

from app.models.product import Product
from app.repositories.base_repository import BaseRepository


class ProductRepository(BaseRepository[Product]):
    def __init__(self, db: AsyncSession):
        super().__init__(Product, db)

    async def get_by_id_and_org(
        self,
        product_id: UUID,
        organization_id: UUID,
    ) -> Product | None:
        result = await self.db.execute(
            select(Product).where(
                Product.id == product_id,
                Product.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_org(
        self,
        organization_id: UUID,
        category: Optional[str] = None,
        include_inactive: bool = False,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Product], int]:
        query = select(Product).where(Product.organization_id == organization_id)

        if not include_inactive:
            query = query.where(Product.is_active == True)
        if category:
            query = query.where(Product.category == category)

        total = await self.db.scalar(
            select(func.count()).select_from(query.subquery())
        )
        result = await self.db.execute(
            query.order_by(Product.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        return result.scalars().all(), total

    async def get_active_by_id_and_org(
        self,
        product_id: UUID,
        organization_id: UUID,
    ) -> Product | None:
        result = await self.db.execute(
            select(Product).where(
                Product.id == product_id,
                Product.organization_id == organization_id,
                Product.is_active == True,
            )
        )
        return result.scalar_one_or_none()