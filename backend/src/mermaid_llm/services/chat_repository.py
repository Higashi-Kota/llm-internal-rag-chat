"""Chat session and message repository for persistence."""

from __future__ import annotations

import json
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mermaid_llm.db.models import ChatMessage, ChatSession


class ChatRepository:
    """Repository for chat session and message persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_session(self, title: str | None = None) -> ChatSession:
        """Create a new chat session."""
        chat_session = ChatSession(title=title)
        self._session.add(chat_session)
        await self._session.flush()
        return chat_session

    async def get_session(self, session_id: UUID) -> ChatSession | None:
        """Get a chat session by ID."""
        result = await self._session.execute(
            select(ChatSession).where(ChatSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def list_sessions(
        self, limit: int = 50, offset: int = 0
    ) -> list[ChatSession]:
        """List chat sessions ordered by most recent."""
        result = await self._session.execute(
            select(ChatSession)
            .order_by(ChatSession.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def update_session_title(
        self, session_id: UUID, title: str
    ) -> ChatSession | None:
        """Update session title."""
        session = await self.get_session(session_id)
        if session:
            session.title = title
            await self._session.flush()
        return session

    async def delete_session(self, session_id: UUID) -> bool:
        """Delete a session and all its messages."""
        session = await self.get_session(session_id)
        if not session:
            return False

        # Delete messages first
        messages = await self.get_messages(session_id)
        for msg in messages:
            await self._session.delete(msg)

        await self._session.delete(session)
        await self._session.flush()
        return True

    async def add_message(
        self,
        session_id: UUID,
        role: str,
        content: str,
        sources: list[dict[str, object]] | None = None,
        model: str | None = None,
        provider: str | None = None,
    ) -> ChatMessage:
        """Add a message to a session."""
        sources_json = json.dumps(sources) if sources else None
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            sources_json=sources_json,
            model=model,
            provider=provider,
        )
        self._session.add(message)
        await self._session.flush()
        return message

    async def get_messages(
        self, session_id: UUID, limit: int | None = None
    ) -> list[ChatMessage]:
        """Get all messages for a session."""
        query = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
        )
        if limit:
            query = query.limit(limit)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_message(self, message_id: UUID) -> ChatMessage | None:
        """Get a message by ID."""
        result = await self._session.execute(
            select(ChatMessage).where(ChatMessage.id == message_id)
        )
        return result.scalar_one_or_none()
