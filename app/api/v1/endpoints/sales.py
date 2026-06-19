from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select, func



from app.core.database import get_db
from app.core.dependencies import get_current_active_staff
from app.models.user import User
from app.schemas.sale import SaleCreate, SaleOut
from app.services.sale_service import SaleService


router = APIRouter()


@router.post("/create-sale", response_model=SaleOut, status_code=201)
async def submit_sale(
    payload: SaleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_staff),
):
    return await SaleService.submit_sale(payload, current_user, db)