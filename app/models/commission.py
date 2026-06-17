import uuid
from enum import Enum as PyEnum
from sqlalchemy import ForeignKey, Numeric, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class CommissionStatus(str, PyEnum):
    PENDING = "pending"
    APPROVED = "approved"
    PAID = "paid"
    DISPUTED = "disputed"


class Commission(Base, TimestampMixin):
    __tablename__ = "commissions"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id"), nullable=False
    )
    staff_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    sale_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sales.id"), nullable=False
    )
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[CommissionStatus] = mapped_column(
        Enum(CommissionStatus), default=CommissionStatus.PENDING
    )
    period: Mapped[str] = mapped_column(String(20), nullable=False) 
    
    notes: Mapped[str] = mapped_column(String(500), nullable=True)

    # relationships
    staff: Mapped["User"] = relationship()
    sale: Mapped["Sale"] = relationship()