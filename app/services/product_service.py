from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional

from app.models.product import Product
from app.models.organization import CommissionModel
from app.core.exceptions import NotFoundException, BadRequestException
from app.schemas.product import ProductCreate, ProductUpdate
from app.schemas.common import PaginatedResponse
from app.repositories.product_repository import ProductRepository
from app.repositories.organization_repository import OrganizationRepository
from app.utils.pagination import paginate


class ProductService:

    @staticmethod
    async def create_product(
        payload: ProductCreate,
        organization_id: UUID,
        db: AsyncSession,
    ) -> Product:
        product_repo = ProductRepository(db)
        org_repo = OrganizationRepository(db)

        org = await org_repo.get_by_id(organization_id)

        # Enforce cost_price when org uses profit-based commissions
        if (
            org
            and org.commission_model == CommissionModel.PROFIT_BASED
            and payload.cost_price is None
        ):
            raise BadRequestException(
                "cost_price is required for profit-based commission organizations"
            )

        # cost_price must be less than price — you can't profit from a loss
        if (
            payload.cost_price is not None
            and payload.cost_price >= payload.price
        ):
            raise BadRequestException(
                "cost_price must be less than the selling price"
            )

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
        return paginate(products, total, page, per_page)

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
        org_repo = OrganizationRepository(db)

        product = await product_repo.get_by_id_and_org(product_id, organization_id)
        if not product:
            raise NotFoundException("Product not found")

        updates = payload.model_dump(exclude_unset=True)

        # If price or cost_price is being updated, re-validate the relationship
        new_price = updates.get("price", float(product.price))
        new_cost = updates.get("cost_price", float(product.cost_price) if product.cost_price else None)

        if new_cost is not None and new_cost >= new_price:
            raise BadRequestException(
                "cost_price must be less than the selling price"
            )

        for field, value in updates.items():
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