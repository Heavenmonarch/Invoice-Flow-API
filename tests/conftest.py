import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import NullPool

from app.core.database import Base, get_db
from app.core.security import hash_password
from app.models.organization import Organization
from app.models.user import User, UserRole
from app.models.product import Product
from main import app


TEST_DATABASE_URL = "postgresql+asyncpg://postgres:Ayanfe12!!@localhost:5432/commission_flow_test_db"


test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture
async def db():
    """
    Wrap each test in an outer transaction + SAVEPOINT, so that any
    db.commit() calls inside fixtures/endpoints only commit the SAVEPOINT,
    not the real transaction. Rolling back the outer connection at the end
    of the test discards everything, guaranteeing full isolation between
    tests even when code under test calls commit().
    """
    async with test_engine.connect() as conn:
        await conn.begin()
        session = AsyncSession(bind=conn, expire_on_commit=False)

        await conn.begin_nested()  # SAVEPOINT

        @event.listens_for(session.sync_session, "after_transaction_end")
        def restart_savepoint(sync_session, transaction):
            if conn.closed:
                return
            if not conn.sync_connection.in_nested_transaction():
                conn.sync_connection.begin_nested()

        try:
            yield session
        finally:
            await session.close()
            await conn.rollback()


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
async def test_admin(db: AsyncSession, test_org: Organization) -> User:
    user = User(
        organization_id=test_org.id,
        email="admin@test.com",
        full_name="Test Admin",
        hashed_password=hash_password("Test@1234"),
        role=UserRole.ADMIN,
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
        email="staff@test.com",
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
async def admin_token(client: AsyncClient, test_admin: User) -> str:
    response = await client.post("/api/v1/auth/login", json={
        "email": "admin@test.com",
        "password": "Test@1234",
    })
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def staff_token(client: AsyncClient, test_staff: User) -> str:
    response = await client.post("/api/v1/auth/login", json={
        "email": "staff@test.com",
        "password": "Test@1234",
    })
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def superadmin_token(client: AsyncClient, test_superadmin: User) -> str:
    response = await client.post("/api/v1/auth/login", json={
        "email": "superadmin@test.com",
        "password": "Test@1234"
    })
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def test_product(db: AsyncSession, test_org) -> Product:
    product = Product(
        organization_id=test_org.id,
        name="Test Product",
        price=100.00,
        commission_rate=10.0,
        is_active=True,
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product