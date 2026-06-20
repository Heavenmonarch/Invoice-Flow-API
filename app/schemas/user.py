import uuid
from pydantic import BaseModel, EmailStr
from app.models.user import UserRole
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    firstname: str
    lastname: str
    password: str
    role: UserRole = UserRole.STAFF
    
    
class UserUpdate(BaseModel):
    firstname: str | None = None
    lastname: str | None = None
    email: EmailStr | None = None
    is_active: bool | None = None
    
class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    organization_id: uuid.UUID
    created_at: datetime
    
    model_config = {"from_attributes": True}