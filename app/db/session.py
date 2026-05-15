from contextlib import contextmanager
from typing import AsyncGenerator, Generator
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.engine import Engine

from app.core.config import settings
from app.db.base import Base


def _make_async_engine() -> AsyncEngine:
    """Create async engine with dialect-appropriate pool settings."""
    engine_kwargs = {
        "echo": settings.DEBUG,
        "future": True,
    }
    if "sqlite" in settings.DATABASE_URL:
        engine_kwargs["poolclass"] = StaticPool
        engine_kwargs["connect_args"] = {"check_same_thread": False}
    else:
        engine_kwargs["pool_size"] = settings.DATABASE_POOL_SIZE
        engine_kwargs["max_overflow"] = settings.DATABASE_MAX_OVERFLOW

    return create_async_engine(settings.DATABASE_URL, **engine_kwargs)


def _make_sync_engine() -> Engine:
    """Create sync engine with dialect-appropriate pool settings."""
    engine_kwargs = {
        "echo": settings.DEBUG,
        "future": True,
    }
    if "sqlite" in settings.DATABASE_SYNC_URL:
        engine_kwargs["poolclass"] = StaticPool
        engine_kwargs["connect_args"] = {"check_same_thread": False}
    else:
        engine_kwargs["pool_size"] = settings.DATABASE_POOL_SIZE
        engine_kwargs["max_overflow"] = settings.DATABASE_MAX_OVERFLOW

    return create_engine(settings.DATABASE_SYNC_URL, **engine_kwargs)


# Async engine for FastAPI
async_engine: AsyncEngine = _make_async_engine()

# Async session factory
AsyncSessionLocal = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# Sync engine for Alembic migrations
sync_engine = _make_sync_engine()


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI routes that need database access."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Initialize database tables (for development/testing only)."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@contextmanager
def get_sync_session() -> Generator[Engine, None, None]:
    """Get a synchronous database connection (for scripts/migrations)."""
    with sync_engine.begin() as conn:
        yield conn
