"""Repository for diagram persistence operations."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mermaid_llm.db.models import Diagram, DiagramStatus

if TYPE_CHECKING:
    from collections.abc import Sequence

logger = logging.getLogger(__name__)


class DiagramRepository:
    """Repository for managing diagram persistence.

    Provides a clean interface for CRUD operations on diagrams,
    abstracting away SQLAlchemy implementation details.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session.

        Args:
            session: An async SQLAlchemy session.
        """
        self._session = session

    async def create(
        self,
        *,
        trace_id: str,
        prompt: str,
        language: str,
        diagram_type: str,
        status: DiagramStatus = DiagramStatus.PENDING,
        mermaid_code: str | None = None,
        error_message: str | None = None,
        model: str | None = None,
        latency_ms: int | None = None,
        attempts: int = 0,
    ) -> Diagram:
        """Create a new diagram record.

        Args:
            trace_id: Unique trace identifier for the request.
            prompt: The user's input prompt.
            language: Detected language code.
            diagram_type: Type of diagram generated.
            status: Current status of the diagram.
            mermaid_code: Generated Mermaid code if available.
            error_message: Error message if generation failed.
            model: Model used for generation.
            latency_ms: Time taken in milliseconds.
            attempts: Number of generation attempts.

        Returns:
            The created Diagram instance.
        """
        diagram = Diagram(
            trace_id=trace_id,
            prompt=prompt,
            language=language,
            diagram_type=diagram_type,
            status=status,
            mermaid_code=mermaid_code,
            error_message=error_message,
            model=model,
            latency_ms=latency_ms,
            attempts=attempts,
        )
        self._session.add(diagram)
        await self._session.flush()
        await self._session.refresh(diagram)
        logger.info(f"Created diagram with id={diagram.id}, trace_id={trace_id}")
        return diagram

    async def get_by_id(self, diagram_id: UUID) -> Diagram | None:
        """Get a diagram by its ID.

        Args:
            diagram_id: The UUID of the diagram.

        Returns:
            The Diagram if found, None otherwise.
        """
        result = await self._session.execute(
            select(Diagram).where(Diagram.id == diagram_id)
        )
        return result.scalar_one_or_none()

    async def get_by_trace_id(self, trace_id: str) -> Sequence[Diagram]:
        """Get all diagrams for a given trace ID.

        Args:
            trace_id: The trace identifier.

        Returns:
            A sequence of Diagram instances ordered by creation time.
        """
        result = await self._session.execute(
            select(Diagram)
            .where(Diagram.trace_id == trace_id)
            .order_by(Diagram.created_at.desc())
        )
        return result.scalars().all()

    async def update(
        self,
        diagram: Diagram,
        *,
        mermaid_code: str | None = None,
        status: DiagramStatus | None = None,
        error_message: str | None = None,
        latency_ms: int | None = None,
        attempts: int | None = None,
    ) -> Diagram:
        """Update an existing diagram.

        Args:
            diagram: The diagram to update.
            mermaid_code: New Mermaid code if changed.
            status: New status if changed.
            error_message: New error message if changed.
            latency_ms: New latency if changed.
            attempts: New attempt count if changed.

        Returns:
            The updated Diagram instance.
        """
        if mermaid_code is not None:
            diagram.mermaid_code = mermaid_code
        if status is not None:
            diagram.status = status
        if error_message is not None:
            diagram.error_message = error_message
        if latency_ms is not None:
            diagram.latency_ms = latency_ms
        if attempts is not None:
            diagram.attempts = attempts

        await self._session.flush()
        await self._session.refresh(diagram)
        logger.info(f"Updated diagram id={diagram.id}, status={diagram.status}")
        return diagram

    async def list_recent(self, limit: int = 50) -> Sequence[Diagram]:
        """List recent diagrams.

        Args:
            limit: Maximum number of diagrams to return.

        Returns:
            A sequence of Diagram instances ordered by creation time descending.
        """
        result = await self._session.execute(
            select(Diagram).order_by(Diagram.created_at.desc()).limit(limit)
        )
        return result.scalars().all()

    async def delete(self, diagram: Diagram) -> None:
        """Delete a diagram.

        Args:
            diagram: The diagram to delete.
        """
        await self._session.delete(diagram)
        await self._session.flush()
        logger.info(f"Deleted diagram id={diagram.id}")
