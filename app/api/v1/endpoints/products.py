from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import uuid

from app.core.database import get_db
from app.core.dependencies import get_current_active_staff, get_current_admin
from app.models.product import Product
from app.models.user import User
from app.schemas.product import ProductCreate, ProductUpdate, ProductOut
from app.schemas.common import PaginatedResponse, DeleteResponse

router = APIRouter()


@router.post("/create-product", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
async def create_product(payload: ProductCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_admin)):
    
    product = Product(**payload.model_dump, organization_id=current_user.organization_id)
    db.add(product)
    
    await db.commit()
    
    await db.refresh(product)
    
    return product


@router.get("/list-products", response_model=PaginatedResponse[ProductOut])
async def list_products (page: int = 1, per_page: int = 20, category: str = None, db: AsyncSession = Depends(get_db), current_user : User = Depends(get_current_active_staff)):
    query = (
        select(Product).where(Product.organization_id == current_user.organization_id).where(Product.is_active == True)
    )
    
    if category:
        query = query.where(Product.category == category)
        
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    results = await db.execute(query.offset((page - 1) * per_page).limit(per_page))
    products = results.scalars().all()
    
    return PaginatedResponse(
        items=products,
        total=total,
        page=page,
        per_page=per_page,
        pages=-(-total // per_page)
    )
    

@router.get("/fetch-product/{product_id}", response_model=ProductOut)
async def get_product(product_id: uuid.UUID, db:AsyncSession = Depends(get_db), current_user:User = Depends(get_current_active_staff)):
    
    result = await db.execute(select(Product).where(Product.id == product_id, Product.organization_id == current_user.organization_id))
    
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return product

@router.patch("/update-product/{product_id}", response_model=ProductOut)
async def update_product(product_id: uuid.UUID, payload: ProductUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_admin)):
    
    result = await db.execute(select(Product).where(Product.id == product_id, Product.organization_id == current_user.organization_id))
    
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
        
    await db.commit()
    await db.refresh(product)
    
    return product


@router.delete("/delete-product/{product_id}", response_model=DeleteResponse)
async def delete_product(product_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_admin)):
    
    result = await db.execute(select(Product).where(Product.id == product_id, Product.organization_id == current_user.organization_id))
    
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    
    await db.delete(product)
    
    await db.commit()
    await db.refresh(product)
    
    return product