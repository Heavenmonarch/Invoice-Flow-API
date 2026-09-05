import uuid
from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.models.organization import CommissionModel


class OrganizationCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    commission_model: Optional[CommissionModel] = None
    show_leaderboard: Optional[bool] = None


class OrganizationOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    email: str
    is_active: bool
    commission_model: CommissionModel
    show_leaderboard: bool
    created_at: datetime

    model_config = {"from_attributes": True}