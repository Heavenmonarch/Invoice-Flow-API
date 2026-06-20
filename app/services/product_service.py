from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status
import uuid


from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate
from app.schemas.common import PaginatedResponse


class ProductService:
    @staticmethod
    async def create_product (
        payload: ProductCreate,
        organization_id: uuid.UUID,
        db: AsyncSession
    ) -> Product:
        product = Product(
            **payload.model_dump(),
            organization_id=organization_id
        )
        db.add(product)
        
        await db.commit()
        
        await db.refresh(product)
        
        return product
    
    @staticmethod
    async def list_products(
        db: AsyncSession, organization_id: uuid.UUID,
        category: str = None,
        include_inactive: bool = False,
        page: int = 1, per_page: int = 20
    ) -> PaginatedResponse:
        query = select(Product).where(Product.organization_id == organization_id)
        
        if not include_inactive:
            query = query.where(Product.is_active == True)
        if category:
            query = query.where(Product.category == category)
            
        total = await db.scalar(select(func.count()).select_from(query.subquery()))
        result = await db.execute(
            query.order_by(Product.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        products = result.scalars().all()

        return PaginatedResponse(
            items=products,
            total=total,
            page=page,
            per_page=per_page,
        )
        
    
    @staticmethod
    async def get_product(
        product_id: uuid.UUID,
        organization_id: uuid.UUID,
        db: AsyncSession,
    ) -> Product:
        result = await db.execute(
            select(Product).where(
                Product.id == product_id,
                Product.organization_id == organization_id,
            )
        )
        product = result.scalar_one_or_none()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )
        return product

    @staticmethod
    async def update_product(
        product_id: uuid.UUID,
        payload: ProductUpdate,
        organization_id: uuid.UUID,
        db: AsyncSession,
    ) -> Product:
        product = await ProductService.get_product(product_id, organization_id, db)

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(product, field, value)

        await db.commit()
        await db.refresh(product)
        return product

    @staticmethod
    async def deactivate_product(
        product_id: uuid.UUID,
        organization_id: uuid.UUID,
        db: AsyncSession,
    ) -> Product:
        product = await ProductService.get_product(product_id, organization_id, db)
        product.is_active = False
        await db.commit()
        await db.refresh(product)
        return product

    @staticmethod
    async def add_image_urls(
        product_id: uuid.UUID,
        organization_id: uuid.UUID,
        urls: list[str],
        db: AsyncSession,
    ) -> Product:
        product = await ProductService.get_product(product_id, organization_id, db)
        existing = product.image_urls or []
        product.image_urls = existing + urls
        await db.commit()
        await db.refresh(product)
        return product