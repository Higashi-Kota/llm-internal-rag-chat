"""Database session management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from mermaid_llm.config import settings


@lru_cache
def get_engine() -> AsyncEngine:
    """Get or create the database engine (lazy initialization)."""
    return create_async_engine(
        settings.effective_database_url,
        echo=settings.debug,
    )


@lru_cache
def get_async_session_maker() -> async_sessionmaker[AsyncSession]:
    """Get or create the session maker (lazy initialization)."""
    return async_sessionmaker(
        get_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
    )


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session with automatic commit/rollback."""
    async with get_async_session_maker()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database session."""
    async with get_session() as session:
        yield session
