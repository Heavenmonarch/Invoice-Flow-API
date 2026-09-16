import uuid
from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime
from app.models.target import TargetType


class TargetCreate(BaseModel):
    staff_id: uuid.UUID
    period: str
    target_type: TargetType
    target_amount: float
    notes: Optional[str] = None

    @field_validator("target_amount")
    @classmethod
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Target amount must be greater than zero")
        return round(v, 2)

    @field_validator("period")
    @classmethod
    def period_must_be_valid(cls, v):
        import re
        if not re.match(r"^\d{4}-\d{2}$", v):
            raise ValueError("Period must be in YYYY-MM format e.g. 2025-06")
        return v


class TargetUpdate(BaseModel):
    target_amount: Optional[float] = None
    notes: Optional[str] = None

    @field_validator("target_amount")
    @classmethod
    def amount_must_be_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Target amount must be greater than zero")
        return round(v, 2) if v is not None else v


class TargetOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    staff_id: uuid.UUID
    period: str
    target_type: TargetType
    target_amount: float
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class TargetProgressOut(BaseModel):
    id: uuid.UUID
    staff_id: uuid.UUID
    full_name: str
    period: str
    target_type: TargetType
    target_amount: float
    current_amount: float
    progress_percent: float
    is_achieved: bool
    notes: Optional[str]