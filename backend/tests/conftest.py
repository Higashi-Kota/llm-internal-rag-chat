"""Pytest configuration and fixtures."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator, Generator
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine

# Set mock mode before importing app
os.environ["USE_MOCK"] = "true"

from mermaid_llm.db.models import Base  # noqa: E402
from mermaid_llm.main import app  # noqa: E402


@pytest.fixture
def mock_settings() -> Generator[None, None, None]:
    """Patch settings to use mock mode."""
    with patch.dict(os.environ, {"USE_MOCK": "true", "OPENAI_API_KEY": ""}):
        yield


@pytest.fixture(scope="session")
def postgres_url() -> str:
    """Get PostgreSQL URL from testcontainers or environment.

    Uses testcontainers when Docker is available, falls back to
    in-memory SQLite for CI environments without Docker.
    """
    # Check if we should use testcontainers
    use_testcontainers = os.environ.get("USE_TESTCONTAINERS", "false").lower() == "true"

    if use_testcontainers:
        try:
            from testcontainers.postgres import (  # type: ignore[import-untyped]
                PostgresContainer,
            )

            # Start PostgreSQL container for the test session
            postgres = PostgresContainer("postgres:16-alpine")
            postgres.start()

            # Get connection URL and convert to async driver
            url = postgres.get_connection_url()
            # Replace psycopg2 with asyncpg
            async_url = url.replace("psycopg2", "asyncpg")

            # Register cleanup
            import atexit

            atexit.register(postgres.stop)

            return async_url
        except ImportError:
            pass  # Fall through to SQLite
        except Exception:
            pass  # Fall through to SQLite

    # Fallback: Use in-memory SQLite for testing without Docker
    return "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def db_engine(postgres_url: str) -> AsyncGenerator[AsyncEngine, None]:
    """Create database engine for tests."""
    engine = create_async_engine(postgres_url, echo=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(
    db_engine: AsyncEngine,
) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for tests."""
    session_maker = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def async_client(
    db_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client for the FastAPI app with DB override."""
    from mermaid_llm.db import get_db

    # Override the database dependency
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    # Clean up dependency override
    app.dependency_overrides.clear()
