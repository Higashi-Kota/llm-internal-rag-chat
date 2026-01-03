"""SQLAlchemy database models."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


class Base(DeclarativeBase):
    """Base class for all database models."""


class DiagramStatus(str, Enum):
    """Diagram generation status."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Diagram(Base):
    """Diagram model for storing generated diagrams.

    Stores the history of all diagram generation requests including
    prompt, generated code, status, and metadata.
    """

    __tablename__ = "diagrams"

    # Primary key with auto-generated UUID
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Required fields (must be provided at creation)
    trace_id: Mapped[str] = mapped_column(index=True)
    prompt: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column()
    diagram_type: Mapped[str] = mapped_column()
    # Use String storage to match migration (not PostgreSQL ENUM)
    status: Mapped[DiagramStatus] = mapped_column(String, nullable=False)

    # Optional fields with explicit defaults
    mermaid_code: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    model: Mapped[str | None] = mapped_column(nullable=True, default=None)
    latency_ms: Mapped[int | None] = mapped_column(nullable=True, default=None)
    attempts: Mapped[int] = mapped_column(default=0)

    # Timestamp fields (timezone=True to match migration TIMESTAMPTZ)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    # Table-level configuration
    __table_args__ = (Index("idx_diagrams_created_at", "created_at"),)


# ============================================================
# RAG Chat Models
# ============================================================


class ChatSession(Base):
    """Chat session for grouping related messages."""

    __tablename__ = "chat_sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    title: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    __table_args__ = (Index("idx_chat_sessions_created_at", "created_at"),)


class ChatMessage(Base):
    """Individual chat message within a session."""

    __tablename__ = "chat_messages"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(index=True)
    role: Mapped[str] = mapped_column(String(20))  # "user" or "assistant"
    content: Mapped[str] = mapped_column(Text)
    sources_json: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    model: Mapped[str | None] = mapped_column(nullable=True, default=None)
    provider: Mapped[str | None] = mapped_column(nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )

    __table_args__ = (
        Index("idx_chat_messages_session_id", "session_id"),
        Index("idx_chat_messages_created_at", "created_at"),
    )
