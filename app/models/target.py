import uuid
from enum import Enum as PyEnum
from typing import Optional
from sqlalchemy import String, Numeric, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class TargetType(str, PyEnum):
    REVENUE = "revenue"      
    COMMISSION = "commission" 


class Target(Base, TimestampMixin):
    __tablename__ = "targets"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id"), nullable=False
    )
    staff_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    period: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # e.g. "2025-06"
    target_type: Mapped[TargetType] = mapped_column(
        Enum(TargetType), nullable=False
    )
    target_amount: Mapped[float] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )

    # One target per staff member per period per type
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "staff_id",
            "period",
            "target_type",
            name="uq_target_staff_period_type",
        ),
    )

    staff: Mapped["User"] = relationship(foreign_keys=[staff_id])
    organization: Mapped["Organization"] = relationship()