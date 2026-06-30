import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool

from app.core.database import Base, get_db
from app.core.security import hash_password
from app.models.organization import Organization
from app.models.user import User, UserRole
from main import app


TEST_DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/commissiontrack_test"


test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)