from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import uuid

from app.core.database import get_db
from app.core.dependencies import get_current_active_staff, get_current_admin
from app.models.user import User
from app.schemas.product import ProductCreate, ProductUpdate, ProductOut
from app.schemas.common import PaginatedResponse
from app.utils.storage import upload_multiple_images
from app.services.product_service import ProductService
from pydantic import BaseModel

router = APIRouter()


class ImageUrlsPayload(BaseModel):
    urls: List[str]


@router.post("/create-product", response_model=ProductOut, status_code=201)
async def create_product(
    payload: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    return await ProductService.create_product(payload, current_user.organization_id, db)


@router.get("/list-products", response_model=PaginatedResponse[ProductOut])
async def list_products(
    page: int = 1,
    per_page: int = 20,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_staff),
):
    return await ProductService.list_products(
        db, current_user.organization_id, category, False, page, per_page
    )


@router.get("/fetch-product/{product_id}", response_model=ProductOut)
async def get_product(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_staff),
):
    return await ProductService.get_product(product_id, current_user.organization_id, db)


@router.patch("/update-product/{product_id}", response_model=ProductOut)
async def update_product(
    product_id: uuid.UUID,
    payload: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    return await ProductService.update_product(
        product_id, payload, current_user.organization_id, db
    )


@router.patch("/deactivate-product/{product_id}/deactivate", response_model=ProductOut)
async def deactivate_product(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    return await ProductService.deactivate_product(
        product_id, current_user.organization_id, db
    )


@router.post("/add-product-image/{product_id}/images", response_model=ProductOut)
async def add_images(
    product_id: uuid.UUID,
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    urls = await upload_multiple_images(files, folder="products")
    
    return await ProductService.add_image_urls(
        product_id, current_user.organization_id, urls, db
    )