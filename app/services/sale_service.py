from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from datetime import datetime, timezone
from uuid import UUID
from typing import Optional

from app.models.sale import Sale
from app.models.commission import Commission, CommissionStatus
from app.models.user import User, UserRole
from app.schemas.sale import SaleCreate
from app.schemas.common import PaginatedResponse
from app.repositories.product_repository import ProductRepository
from app.repositories.sale_repository import SaleRepository
from app.repositories.commission_repository import CommissionRepository


class SaleService:

    @staticmethod
    async def submit_sale(
        payload: SaleCreate,
        current_user: User,
        db: AsyncSession,
    ) -> Sale:
        product_repo = ProductRepository(db)
        sale_repo = SaleRepository(db)
        commission_repo = CommissionRepository(db)

        product = await product_repo.get_active_by_id_and_org(
            payload.product_id, current_user.organization_id
        )
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found or is inactive",
            )

        unit_price = float(product.price)
        commission_rate = float(product.commission_rate)
        total_amount = round(unit_price * payload.quantity, 2)
        commission_amount = round(total_amount * (commission_rate / 100), 2)
        period = datetime.now(timezone.utc).strftime("%Y-%m")

        sale = Sale(
            organization_id=current_user.organization_id,
            staff_id=current_user.id,
            product_id=product.id,
            quantity=payload.quantity,
            unit_price=unit_price,
            total_amount=total_amount,
            commission_rate=commission_rate,
            commission_amount=commission_amount,
            notes=payload.notes,
        )
        sale = await sale_repo.create(sale)

        commission = Commission(
            organization_id=current_user.organization_id,
            staff_id=current_user.id,
            sale_id=sale.id,
            amount=commission_amount,
            status=CommissionStatus.PENDING,
            period=period,
        )
        await commission_repo.create(commission)
        await db.commit()
        await db.refresh(sale)
        return sale

    @staticmethod
    async def list_sales(
        db: AsyncSession,
        organization_id: UUID,
        staff_id: Optional[UUID] = None,
        product_id: Optional[UUID] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> PaginatedResponse:
        sale_repo = SaleRepository(db)
        sales, total = await sale_repo.list_by_org(
            organization_id, staff_id, product_id,
            date_from, date_to, page, per_page,
        )
        return PaginatedResponse(
            items=sales,
            total=total,
            page=page,
            per_page=per_page,
            pages=-(-total // per_page),
        )

    @staticmethod
    async def get_sale(
        sale_id: UUID,
        current_user: User,
        db: AsyncSession,
    ) -> Sale:
        sale_repo = SaleRepository(db)

        if current_user.role == UserRole.STAFF:
            sale = await sale_repo.get_by_id_and_org(sale_id, current_user.organization_id)
            if not sale or sale.staff_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Sale not found",
                )
            return sale

        sale = await sale_repo.get_by_id_and_org(sale_id, current_user.organization_id)
        if not sale:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sale not found",
            )
        return sale