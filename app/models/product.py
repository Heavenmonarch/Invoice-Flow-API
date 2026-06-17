import uuid
from sqlalchemy import String, Text, Numeric, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class Product(Base, TimestampMixin):
    __tablename__ = "products"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id"), nullable=False
    )
    
    name: Mapped[str] = mapped_column(String(75), nullable=False)
    
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    category: Mapped[str] = mapped_column(String(100), nullable=True)
    
    price: Mapped[float] = mapped_column(Numeric(12,2), nullable=False)
    
    commission_rate: Mapped[float] = mapped_column(Numeric(5,2), nullable=False)
    
    image_urls: Mapped[list] = mapped_column(JSON, default=list)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # relationships
    
    organization: Mapped["Organization"] = relationship(back_populates="products")
    sales: Mapped[list["Sale"]] = relationship(back_populates="product")