import uuid
from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class Sale(Base, TimestampMixin):
    __tablename__: "sales"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id"), nullable=False
    )
    
    staff_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    
    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id"), nullable=False
    )
    
    quantity: Mapped[int] = mapped_column (Integer, nullable=False)
    
    unit_price: Mapped[float] = mapped_column(Numeric(12,2), nullable=False)
    
    total_amount: Mapped[float] = mapped_column(Numeric(12,2), nullable=False)
    
    commission_rate: Mapped[float] = mapped_column(Numeric(5,2), nullable=False)
    
    commission_amount: Mapped[float] =mapped_column(Numeric(12,2), nullable=False)
    
    notes: Mapped[str] = mapped_column(String(500), nullable=True)
    
    
    # relationships
    organization: Mapped["Organization"] = relationship()
    staff: Mapped["User"] = relationship(back_populates="sales")
    product: Mapped["Product"] = relationship(back_populates="sales")