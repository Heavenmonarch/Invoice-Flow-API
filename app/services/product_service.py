from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional

from app.models.product import Product
from app.core.exceptions import NotFoundException
from app.schemas.product import ProductCreate, ProductUpdate
from app.schemas.common import PaginatedResponse
from app.repositories.product_repository import ProductRepository


class ProductService:

    @staticmethod
    async def create_product(
        payload: ProductCreate,
        organization_id: UUID,
        db: AsyncSession,
    ) -> Product:
        product_repo = ProductRepository(db)

        product = Product(
            **payload.model_dump(),
            organization_id=organization_id,
        )
        product = await product_repo.create(product)
        await db.commit()
        await db.refresh(product)
        return product

    @staticmethod
    async def list_products(
        db: AsyncSession,
        organization_id: UUID,
        category: Optional[str] = None,
        include_inactive: bool = False,
        page: int = 1,
        per_page: int = 20,
    ) -> PaginatedResponse:
        product_repo = ProductRepository(db)
        products, total = await product_repo.list_by_org(
            organization_id, category, include_inactive, page, per_page
        )
        return PaginatedResponse(
            items=products,
            total=total,
            page=page,
            per_page=per_page,
            pages=-(-total // per_page),
        )

    @staticmethod
    async def get_product(
        product_id: UUID,
        organization_id: UUID,
        db: AsyncSession,
    ) -> Product:
        product_repo = ProductRepository(db)
        product = await product_repo.get_by_id_and_org(product_id, organization_id)
        if not product:
            raise NotFoundException("Product not found")
        return product

    @staticmethod
    async def update_product(
        product_id: UUID,
        payload: ProductUpdate,
        organization_id: UUID,
        db: AsyncSession,
    ) -> Product:
        product_repo = ProductRepository(db)
        product = await product_repo.get_by_id_and_org(product_id, organization_id)

        if not product:
            raise NotFoundException("Product not found")

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(product, field, value)

        return await product_repo.save(product)

    @staticmethod
    async def deactivate_product(
        product_id: UUID,
        organization_id: UUID,
        db: AsyncSession,
    ) -> Product:
        product_repo = ProductRepository(db)
        product = await product_repo.get_by_id_and_org(product_id, organization_id)

        if not product:
            raise NotFoundException("Product not found")

        product.is_active = False
        return await product_repo.save(product)

    @staticmethod
    async def add_image_urls(
        product_id: UUID,
        organization_id: UUID,
        urls: list[str],
        db: AsyncSession,
    ) -> Product:
        product_repo = ProductRepository(db)
        product = await product_repo.get_by_id_and_org(product_id, organization_id)

        if not product:
            raise NotFoundException("Product not found")

        product.image_urls = (product.image_urls or []) + urls
        return await product_repo.save(product)