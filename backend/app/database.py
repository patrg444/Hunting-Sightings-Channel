"""Database connection and session management."""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool
from typing import AsyncGenerator
from app.config import get_settings

settings = get_settings()

# Create async engine
# Disable prepared statements for pgbouncer compatibility by appending to URL
database_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
if "?" in database_url:
    database_url += "&prepared_statement_cache_size=0"
else:
    database_url += "?prepared_statement_cache_size=0"

if settings.debug:
    # Use NullPool for debugging (no pooling)
    engine = create_async_engine(
        database_url,
        echo=settings.debug,
        future=True,
        poolclass=NullPool,
    )
else:
    # Use connection pooling in production
    engine = create_async_engine(
        database_url,
        echo=settings.debug,
        future=True,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
    )

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Create declarative base
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
