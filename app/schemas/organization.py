import uuid
from pydantic import BaseModel, EmailStr
from datetime import datetime


class OrganizationCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    
    
class OrganizationOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    email: str
    is_active: bool
    created_at: datetime
    
    model_config = {"from_attributes": True}
    
class OrganizationUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None