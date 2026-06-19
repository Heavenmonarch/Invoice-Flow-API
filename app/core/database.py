from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=3600,
)


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


async def init_db():
    logger.info("Connecting to database...")
    from app.models.organization import Organization
    from app.models.commission import Commission
    from app.models.product import Product
    from app.models.sale import Sale
    from app.models.user import User
    
    async with engine.begin() as conn:
        logger.info("Database connection established.")
        await conn.run_sync(Base.metadata.create_all)
        

async def close_db():
    logger.info("Closing database connection...")
    await engine.dispose()
    logger.info("Database connection closed.")
    
    
# creating db dependency
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except:
            await session.rollback()
            raise
        finally:
            await session.close()