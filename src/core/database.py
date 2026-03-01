from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker | None = None


def _get_session_factory() -> async_sessionmaker:
    global _engine, _session_factory
    if _session_factory is None:
        from src.config import get_settings
        _engine = create_async_engine(
            get_settings().database_url,
            pool_size=5,
            max_overflow=15,
            pool_pre_ping=True,
            echo=False
        )
        _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    return _session_factory


def async_session() -> AsyncSession:
    return _get_session_factory()()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with _get_session_factory()() as session:
        yield session


async def dispose_engine() -> None:
    """Dispose the engine and reset the session factory.

    Called by Celery tasks before their asyncio event loop closes, to cleanly
    release asyncpg connections tied to that loop.
    """
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None
