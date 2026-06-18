import uuid
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.commission import CommissionStatus


class CommissionUpdate(BaseModel):
    status: CommissionStatus
    notes: Optional[str] = None


class CommissionOut(BaseModel):
    id: uuid.UUID
    staff_id: uuid.UUID
    sale_id: uuid.UUID
    amount: float
    status: CommissionStatus
    period: str
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class CommissionSummary(BaseModel):
    staff_id: uuid.UUID
    full_name: str
    period: str
    total_sales: int
    total_amount: float
    total_commission: float
    status: CommissionStatus