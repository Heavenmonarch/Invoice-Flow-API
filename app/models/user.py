import uuid
from enum import Enum as PyEnum
from sqlalchemy import String, Boolean, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class UserRole(str, PyEnum):
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    STAFF = "staff"
    

class User (Base, TimestampMixin):
    __tablename__: "users"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    
    email: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    
    full_name: Mapped[str] = mapped_column(String(50), nullable=False)
    
    password: Mapped[str] = mapped_column(String(50), nullable=False)
    
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.STAFF,nullable=False,
    )
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    
    organization: Mapped["Organization"] = relationship(back_populates="users")
    sales: Mapped[list["Sale"]] = relationship(back_populates="staff")
