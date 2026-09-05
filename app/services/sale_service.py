from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from uuid import UUID
from typing import Optional

from app.models.sale import Sale
from app.models.commission import Commission, CommissionStatus
from app.models.organization import CommissionModel
from app.models.user import User, UserRole
from app.core.exceptions import NotFoundException, BadRequestException
from app.schemas.sale import SaleCreate
from app.schemas.common import PaginatedResponse
from app.repositories.product_repository import ProductRepository
from app.repositories.sale_repository import SaleRepository
from app.repositories.commission_repository import CommissionRepository
from app.repositories.organization_repository import OrganizationRepository
from app.utils.pagination import paginate
from app.utils.date import current_period


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
        org_repo = OrganizationRepository(db)

        # Fetch product
        product = await product_repo.get_active_by_id_and_org(
            payload.product_id, current_user.organization_id
        )
        if not product:
            raise NotFoundException("Product not found or is inactive")

        # Fetch organization to determine commission model
        org = await org_repo.get_by_id(current_user.organization_id)
        commission_model = org.commission_model if org else CommissionModel.PRICE_BASED

        # Snapshot values
        unit_price = round(float(product.price), 2)
        cost_price = round(float(product.cost_price), 2) if product.cost_price else None
        commission_rate = round(float(product.commission_rate), 2)
        total_amount = round(unit_price * payload.quantity, 2)
        period = current_period()

        # Branch on commission model
        if commission_model == CommissionModel.PROFIT_BASED:
            if cost_price is None:
                raise BadRequestException(
                    "This product has no cost price set — "
                    "cannot calculate profit-based commission"
                )
            profit_amount = round(
                (unit_price - cost_price) * payload.quantity, 2
            )
            commission_amount = round(
                profit_amount * (commission_rate / 100), 2
            )
        else:
            # Price-based — original behaviour
            profit_amount = None
            commission_amount = round(
                total_amount * (commission_rate / 100), 2
            )

        sale = Sale(
            organization_id=current_user.organization_id,
            staff_id=current_user.id,
            product_id=product.id,
            quantity=payload.quantity,
            unit_price=unit_price,
            cost_price=cost_price,
            total_amount=total_amount,
            profit_amount=profit_amount,
            commission_rate=commission_rate,
            commission_amount=commission_amount,
            commission_model=commission_model.value,
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
        return paginate(sales, total, page, per_page)

    @staticmethod
    async def get_sale(
        sale_id: UUID,
        current_user: User,
        db: AsyncSession,
    ) -> Sale:
        sale_repo = SaleRepository(db)
        sale = await sale_repo.get_by_id_and_org(
            sale_id, current_user.organization_id
        )

        if not sale:
            raise NotFoundException("Sale not found")

        if (
            current_user.role == UserRole.STAFF
            and sale.staff_id != current_user.id
        ):
            raise NotFoundException("Sale not found")

        return sale