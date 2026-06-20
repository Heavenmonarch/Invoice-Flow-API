from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status
from datetime import datetime, timezone
import uuid

from app.models.sale import Sale
from app.models.product import Product
from app.models.commission import Commission, CommissionStatus
from app.models.user import User
from app.schemas.sale import SaleCreate, SaleOut
from app.schemas.common import PaginatedResponse


class SaleService:
    
    @staticmethod
    async def submit_sale(payload: SaleCreate, current_user: User, db: AsyncSession) -> Sale:
        result = await db.execute(select(Product).where(Product.id == payload.product_id, Product.organization_id == current_user.organization_id, Product.is_active == True))
        
        product = result.scalar_one_or_none()
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
            
        unit_price = float(product.price)
        commission_rate = float(product.commission_rate)
        
        total_amount = round(unit_price * payload.quantity, 2)
        commission_amount = round(total_amount * (commission_rate/100), 2)
        
        now = datetime.now(timezone.utc)
        period = now.strftime("%Y-%m")
        
        # creating the sale record after getting prerequired data
        sale = Sale(
            organization_id=current_user.organization_id,
            staff_id=current_user.id,
            quantity=payload.quantity,
            unit_price=unit_price,
            total_amount=total_amount,
            commission_rate=commission_rate,
            commission_amount=commission_amount,
            notes=payload.notes
        )
        
        db.add(sale)
        await db.flush()
        
        # Auto-create commission record after a sale record has been creatd innit
        commission = Commission(
            organization_id = current_user.organization_id,
            staff_id=current_user.id,
            sale_id=sale.id,
            amount=commission_amount,
            status=CommissionStatus.PENDING,
            period=period,
        )
        
        db.add(commission)
        await db.commit()
        await db.refresh(sale)
        return sale
    
    
    @staticmethod
    async def list_sales(
        db: AsyncSession, organization_id: uuid.UUID,
        staff_id: uuid.UUID = None, product_id: uuid.UUID = None,
        date_from: datetime = None, date_to: datetime = None,
        page: int = 1, per_page: int = 20
    ) -> PaginatedResponse:
        
        query = select(Sale).where(Sale.organization_id == organization_id)
        
        if staff_id:
            query = query.where(Sale.staff_id == staff_id)
        if product_id:
            query = query.where(Sale.product_id == product_id)
        if date_from:
            query = query.where(Sale.created_at >= date_from)
        if date_to:
            query = query.where(Sale.created_at <= date_to)
            
        
        total = await db.scalar(select(func.count()).select_from(query.subquery()))
        result = await db.execute(
            query.order_by(Sale.created_at.desc())
            .offset((page-1) * per_page)
            .limit(per_page)
        )
        sales = result.scalars().all()
        
        return PaginatedResponse(
            items=sales,
            total=total,
            page=page,
            per_page=per_page,
            pages=-(-total // per_page)
        )
        
    @staticmethod
    async def get_sale(
        sale_id: uuid.UUID,
        current_user: User,
        db: AsyncSession,
    ) -> Sale:
        from app.models.user import UserRole
        query = select(Sale).where(
            Sale.id == sale_id,
            Sale.organization_id == current_user.organization_id,
        )
    
        if current_user.role == UserRole.STAFF:
            query = query.where(Sale.staff_id == current_user.id)

        result = await db.execute(query)
        sale = result.scalar_one_or_none()
        if not sale:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sale not found",
            )
        return sale