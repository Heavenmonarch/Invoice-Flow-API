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


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        

@pytest_asyncio.fixture
async def db():
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()
        

@pytest_asyncio.fixture
async def client(db: AsyncSession):
    async def override_get_db():
        yield db
        
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
        
    app.dependency_overrides.clear()
    

@pytest_asyncio.fixture
async def test_org(db: AsyncSession) -> Organization:
    org = Organization(
        name="Test Organization",
        slug="test-organization",
        email="org@test.com",
        is_active=True
    )
    db.add(org)
    await db.commit()
    await db.refresh(org)
    return org


@pytest_asyncio.fixture
async def test_superadmin(db: AsyncSession, test_org: Organization) -> User:
    user = User(
        organization_id=test_org.id,
        email="superadmin@test.com",
        full_name="Test Superadmin",
        hashed_password=hash_password("Test@1234"),
        role=UserRole.SUPERADMIN,
        is_active=True
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_admin(db: AsyncSession, test_org: Organization) -> User :
    user = User(
        organization_id=test_org.id,
        email="admin@test.com",
        full_name="Test Admin",
        hashed_password=hash_password("Test@1234"),
        role=UserRole.Admin,
        is_active=True,
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_staff(db: AsyncSession, test_org: Organization) -> User:
    user = User(
        organization_id=test_org.id,
        emal="staf@test.com",
        full_name="Test Staff",
        hashed_password=hash_password("Test@1234"),
        role=UserRole.STAFF,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user



@pytest_asyncio.fixture
async def admin_token(client: AsyncClient) -> str:
    response = await client.post("/api/v1/auth/login", json={
        "email": "admin@test.com",
        "password": "Test@1234",
    })
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def staff_token(client: AsyncClient) -> str:
    response = await client.post("/ap1/v1/auth/login", json={
        "email": "staff@test.com",
        "password": "Test@1234",
    })
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def superadmin_token(client: AsyncClient) -> str:
    response = await client.post("/api/v1/auth/login", json={
        "email": "superadmin@test.com",
        "password": "Test@1234"
    })
    return response.json()["access_token"]