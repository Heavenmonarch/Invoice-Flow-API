import uuid
from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import datetime


class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    price: float
    commission_rate: float
    image_urls: List[str] = []
    
    @field_validator("price")
    @classmethod
    def price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Price must be greater than zero")
        return round (v, 2)
    
    @field_validator("commission_rate")
    @classmethod
    def commision_rate_must_be_valid(cls, v):
        if not (0 < v <= 100):
            raise ValueError("Commission rate must be between 0 and 100")
        

class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    price: float | None = None
    commission_rate: float | None = None
    image_urls: List[str] | None = None
    is_active: bool | None = None
    
    
    
class ProductOut(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    category: Optional[str]
    price: float
    commission_rate: float
    image_urls: List[str]
    is_active: bool
    
    model_config = {"from_attributes": True}