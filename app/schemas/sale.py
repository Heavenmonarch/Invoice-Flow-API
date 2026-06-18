import uuid
from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


class SaleCreate(BaseModel):
    product_id: uuid.UUID
    quantity: int
    notes: Optional[str] = None
    
    @field_validator("quantity")
    @classmethod
    def quantity_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Quantity must be at least 1")
        return v
    

class SaleOut(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    staff_id: uuid.UUID
    quantity: int
    unit_price: float
    total_amount: float
    commission_rate: float
    commission_amount: float
    notes: Optional[str]
    created_at: datetime
    
    
    model_config = {"from_attributes": True}