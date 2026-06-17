import uuid
from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class Sale(Base, TimestampMixin):
    __tablename__: "sales"
    
    id: Maped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)