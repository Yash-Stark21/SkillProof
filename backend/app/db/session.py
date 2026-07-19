"""Async SQLAlchemy engine and one-session-per-unit-of-work lifecycle."""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings


def build_async_engine(database_url: str) -> AsyncEngine:
    """Build an engine without opening a connection eagerly."""

    return create_async_engine(database_url, pool_pre_ping=True)


engine = build_async_engine(get_settings().database_url)
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """Yield a session owned by exactly one request or background task."""

    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def dispose_engine() -> None:
    """Release pooled connections during application shutdown."""

    await engine.dispose()
