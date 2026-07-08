from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
import uuid

from app.core.database import get_db
from app.core.dependencies import get_current_active_staff, get_current_admin
from app.models.user import User
from app.schemas.sale import SaleCreate, SaleOut
from app.schemas.common import PaginatedResponse
from app.services.sale_service import SaleService

router = APIRouter()


@router.post("/submit-sale", response_model=SaleOut, status_code=201)
async def submit_sale(
    payload: SaleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_staff),
):
    return await SaleService.submit_sale(payload, current_user, db)

 
@router.get("/list-sales", response_model=PaginatedResponse[SaleOut])
async def list_sales(
    page: int = 1,
    per_page: int = 20,
    staff_id: Optional[uuid.UUID] = None,
    product_id: Optional[uuid.UUID] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    return await SaleService.list_sales(
        db, current_user.organization_id,
        staff_id, product_id, date_from, date_to,
        page, per_page,
    )


@router.get("/my-sales", response_model=PaginatedResponse[SaleOut])
async def my_sales(
    page: int = 1,
    per_page: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_staff),
):
    return await SaleService.list_sales(
        db, current_user.organization_id,
        staff_id=current_user.id,
        page=page,
        per_page=per_page,
    )


@router.get("/fetch-sale/{sale_id}", response_model=SaleOut)
async def get_sale(
    sale_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_staff),
):
    return await SaleService.get_sale(sale_id, current_user, db)