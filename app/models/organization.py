import uuid
from enum import Enum as PyEnum
from sqlalchemy import String, Boolean, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class CommissionModel(str, PyEnum):
    PRICE_BASED = "price_based"
    PROFIT_BASED = "profit_based"


class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    commission_model: Mapped[CommissionModel] = mapped_column(
        Enum(CommissionModel),
        default=CommissionModel.PRICE_BASED,
        nullable=False,
    )

    users: Mapped[list["User"]] = relationship(back_populates="organization")
    products: Mapped[list["Product"]] = relationship(back_populates="organization")