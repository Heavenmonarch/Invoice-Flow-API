from pydantic import BaseModel
from typing import Optional
import uuid


class LeaderboardEntry(BaseModel):
    rank: int
    staff_id: uuid.UUID
    full_name: str
    email: Optional[str] = None
    total_sales: int
    total_revenue: float
    total_commission: float


class LeaderboardResponse(BaseModel):
    period: str
    organization_name: str
    commission_model: str
    entries: list[LeaderboardEntry]