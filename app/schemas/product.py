import uuid
from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import datetime


class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    price: float
    cost_price: Optional[float] = None
    commission_rate: float
    image_urls: List[str] = []

    @field_validator("price")
    @classmethod
    def price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Price must be greater than zero")
        return round(v, 2)

    @field_validator("cost_price")
    @classmethod
    def cost_price_must_be_positive(cls, v):
        if v is not None and v < 0:
            raise ValueError("Cost price cannot be negative")
        return round(v, 2) if v is not None else v

    @field_validator("commission_rate")
    @classmethod
    def commission_rate_must_be_valid(cls, v):
        if not (0 < v <= 100):
            raise ValueError("Commission rate must be between 0 and 100")
        return round(v, 2)


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    cost_price: Optional[float] = None
    commission_rate: Optional[float] = None
    image_urls: Optional[List[str]] = None
    is_active: Optional[bool] = None


class ProductOut(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    category: Optional[str]
    price: float
    cost_price: Optional[float]
    commission_rate: float
    image_urls: List[str]
    is_active: bool
    organization_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}