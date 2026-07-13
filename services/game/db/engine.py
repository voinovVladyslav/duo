from contextlib import asynccontextmanager

from opentelemetry.instrumentation.sqlalchemy import (  # pyright: ignore[reportMissingTypeStubs]
    SQLAlchemyInstrumentor,
)
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from services.game.config import settings

_engine = create_async_engine(
    str(settings.db_dsn),
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_pre_ping=True,
    pool_recycle=1800,
)
SQLAlchemyInstrumentor().instrument(engine=_engine.sync_engine)


def get_async_engine() -> AsyncEngine:
    return _engine


def get_async_session() -> AsyncSession:
    return AsyncSession(get_async_engine())


@asynccontextmanager
async def get_session_ctx(session: AsyncSession | None = None):
    if session is not None:
        yield session
    else:
        async with get_async_session() as s:
            yield s
