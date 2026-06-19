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
    