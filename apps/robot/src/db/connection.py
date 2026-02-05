"""
DoruMake Database Connection
SQLAlchemy async connection management
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text

from src.config import settings

# Create async engine
engine = create_async_engine(
    settings.database.async_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database connection (tables should already exist in production)"""
    from src.utils.logger import logger
    try:
        # Just verify connection works, don't create tables
        # Tables are managed by direct SQL migrations
        async with engine.begin() as conn:
            # Simple connection test
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection verified successfully")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise


async def close_db():
    """Close database connections"""
    await engine.dispose()
