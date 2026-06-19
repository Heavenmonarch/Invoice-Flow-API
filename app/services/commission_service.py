from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status
import uuid


from app.models.commission import Commission, CommissionStatus
from app.models.user import User
from app.schemas.commission import CommissionUpdate, CommissionSummary
from app.schemas.common import PaginatedResponse


class ComissionService:
    
    @staticmethod
    async def list_commission (db: AsyncSession, organzation_id: uuid.UUID, staff_id: uuid.UUID = None, period: str = None, commission_status:  CommissionStatus = None, page: int = 1, per_page: int = 20) -> PaginatedResponse:
        
        query = select(Commission).where(Commission.organization_id == organzation_id)
        
        if staff_id:
            query = query.where(Commission.staff_id == staff_id)
        if period:
            query = query.where(Commission.period == period)
        if commission_status:
            query = query.where(Commission.status == commission_status)
            
        total = await db.scalar(select(func.count()).select_from(query.subquery))
        result = await db.execute(
            query.order_by(Commission.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        commissions = result.scalars().all()
        
        return PaginatedResponse(
            items=commissions,
            total=total,
            page=page,
            per_page=per_page,
            pages=-(total // per_page)
        )
        
        
    

        
        