"""RAG chat API router."""

# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false
# LangChain/RAG types are not fully annotated

from __future__ import annotations

import json
import logging
import time
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from mermaid_llm.api.error_codes import (
    ErrorCode,
    get_error_category,
    get_error_message,
    is_retryable,
)
from mermaid_llm.api.schemas import (
    ChatMessageResponse,
    ChatSessionCreate,
    ChatSessionList,
    ChatSessionResponse,
    ChatSessionWithMessages,
    IndexRequest,
    IndexResponse,
    RAGChatRequest,
    RAGChatResponse,
    SourceInfoResponse,
)
from mermaid_llm.db import get_db
from mermaid_llm.db.models import ChatMessage, ChatSession
from mermaid_llm.rag import get_indexer, rag_settings, stream_rag
from mermaid_llm.rag.retriever import SourceInfo
from mermaid_llm.services import ChatRepository

# FastAPI dependency type alias
DbSession = Annotated[AsyncSession, Depends(get_db)]

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rag", tags=["rag"])


# ============================================================
# Helper functions
# ============================================================


def source_info_to_response(source: SourceInfo) -> SourceInfoResponse:
    """Convert SourceInfo to response schema."""
    return SourceInfoResponse(
        filename=source.filename,
        page=source.page,
        slide=source.slide,
        sheet=source.sheet,
        score=source.score,
    )


def session_to_response(session: ChatSession) -> ChatSessionResponse:
    """Convert ChatSession model to response schema."""
    return ChatSessionResponse(
        id=str(session.id),
        title=session.title,
        created_at=session.created_at.isoformat(),
        updated_at=session.updated_at.isoformat(),
    )


def message_to_response(message: ChatMessage) -> ChatMessageResponse:
    """Convert ChatMessage model to response schema."""
    sources = None
    if message.sources_json:
        sources_data = json.loads(message.sources_json)
        sources = [SourceInfoResponse(**s) for s in sources_data]
    return ChatMessageResponse(
        id=str(message.id),
        role=message.role,
        content=message.content,
        sources=sources,
        model=message.model,
        provider=message.provider,
        created_at=message.created_at.isoformat(),
    )


def create_error_event(
    code: ErrorCode,
    trace_id: str,
    event_id: int,
    details: list[str] | None = None,
) -> dict[str, Any]:
    """Create a structured error event."""
    return {
        "id": f"{trace_id}:{event_id}",
        "event": "error",
        "data": json.dumps(
            {
                "code": code.value,
                "category": get_error_category(code).value,
                "message": get_error_message(code),
                "details": details,
                "trace_id": trace_id,
                "retryable": is_retryable(code),
            }
        ),
    }


@router.post("/chat", response_model=RAGChatResponse)
async def rag_chat(
    request: RAGChatRequest,
    db: DbSession,
) -> RAGChatResponse:
    """RAG chat endpoint (non-streaming).

    Retrieves relevant documents and generates a response.
    If session_id is provided, persists messages to database.
    """
    from mermaid_llm.rag import run_rag

    repo = ChatRepository(db)
    session_id: UUID | None = None

    # Get or create session
    if request.session_id:
        try:
            session_id = UUID(request.session_id)
            session = await repo.get_session(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
        except ValueError as e:
            raise HTTPException(
                status_code=400, detail="Invalid session ID format"
            ) from e

    # Convert messages to chat history format
    chat_history = [
        {"role": msg.role, "content": msg.content} for msg in request.messages[:-1]
    ]
    query = request.messages[-1].content

    # Save user message if session exists
    if session_id:
        await repo.add_message(session_id, "user", query)

    try:
        result = await run_rag(query, chat_history)
    except Exception as e:
        logger.exception(f"RAG chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

    sources = [source_info_to_response(s) for s in result.get("sources", [])]
    response_text = result.get("response", "")
    model = result.get("model", rag_settings.llm_model)
    provider = result.get("provider", rag_settings.llm_provider)

    # Save assistant message if session exists
    if session_id:
        sources_data: list[dict[str, object]] = [
            {
                "filename": s.filename,
                "page": s.page,
                "slide": s.slide,
                "sheet": s.sheet,
                "score": s.score,
            }
            for s in result.get("sources", [])
        ]
        await repo.add_message(
            session_id, "assistant", response_text, sources_data, model, provider
        )
        await db.commit()

    return RAGChatResponse(
        response=response_text,
        sources=sources,
        model=model,
        provider=provider,
        session_id=str(session_id) if session_id else None,
    )


@router.post("/chat/stream")
async def rag_chat_stream(
    request: RAGChatRequest,
    db: DbSession,
) -> EventSourceResponse:
    """RAG chat endpoint with SSE streaming.

    If session_id is provided, persists messages to database.
    """
    repo = ChatRepository(db)
    session_id: UUID | None = None

    # Validate session_id before starting stream
    if request.session_id:
        try:
            session_id = UUID(request.session_id)
            session = await repo.get_session(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
        except ValueError as e:
            raise HTTPException(
                status_code=400, detail="Invalid session ID format"
            ) from e

    # Extract query from messages
    query = request.messages[-1].content

    # Save user message before streaming
    if session_id:
        await repo.add_message(session_id, "user", query)
        await db.commit()

    async def event_generator() -> AsyncGenerator[dict[str, Any], None]:
        trace_id = str(uuid4())
        start = time.perf_counter()
        event_id = 0

        # Convert messages to chat history format
        chat_history = [
            {"role": msg.role, "content": msg.content} for msg in request.messages[:-1]
        ]

        # Send meta event first
        event_id += 1
        yield {
            "id": f"{trace_id}:{event_id}",
            "event": "meta",
            "data": json.dumps(
                {
                    "trace_id": trace_id,
                    "model": rag_settings.llm_model,
                    "provider": rag_settings.llm_provider,
                    "session_id": str(session_id) if session_id else None,
                }
            ),
        }

        try:
            sources_sent = False
            last_response = ""
            final_response = ""
            final_sources: list[dict[str, object]] = []
            final_model = rag_settings.llm_model
            final_provider = rag_settings.llm_provider

            async for update in stream_rag(query, chat_history):
                event_type = update.get("event")

                if event_type == "sources" and not sources_sent:
                    # Send sources event
                    event_id += 1
                    sources = update.get("sources", [])
                    yield {
                        "id": f"{trace_id}:{event_id}",
                        "event": "sources",
                        "data": json.dumps(
                            {
                                "sources": [
                                    {
                                        "filename": s.filename,
                                        "page": s.page,
                                        "slide": s.slide,
                                        "sheet": s.sheet,
                                        "score": s.score,
                                    }
                                    for s in sources
                                ]
                            }
                        ),
                    }
                    sources_sent = True

                elif event_type == "chunk":
                    # Send chunk event
                    response = update.get("response", "")
                    if response != last_response:
                        event_id += 1
                        # Send only the new content
                        new_content = response[len(last_response) :]
                        if new_content:
                            yield {
                                "id": f"{trace_id}:{event_id}",
                                "event": "chunk",
                                "data": json.dumps({"text": new_content}),
                            }
                        last_response = response

                elif event_type == "done":
                    # Capture final values for persistence
                    final_response = update.get("response", "")
                    sources = update.get("sources", [])
                    final_sources = [
                        {
                            "filename": s.filename,
                            "page": s.page,
                            "slide": s.slide,
                            "sheet": s.sheet,
                            "score": s.score,
                        }
                        for s in sources
                    ]
                    final_model = update.get("model", rag_settings.llm_model)
                    final_provider = update.get("provider", rag_settings.llm_provider)

                    # Send done event
                    latency_ms = int((time.perf_counter() - start) * 1000)
                    event_id += 1
                    yield {
                        "id": f"{trace_id}:{event_id}",
                        "event": "done",
                        "data": json.dumps(
                            {
                                "response": final_response,
                                "sources": final_sources,
                                "model": final_model,
                                "provider": final_provider,
                                "latency_ms": latency_ms,
                                "trace_id": trace_id,
                            }
                        ),
                    }

            # Save assistant message after streaming completes
            if session_id and final_response:
                await repo.add_message(
                    session_id,
                    "assistant",
                    final_response,
                    final_sources,
                    final_model,
                    final_provider,
                )
                await db.commit()

        except Exception as e:
            logger.exception(f"Error during RAG streaming: {e}")
            event_id += 1
            yield create_error_event(
                ErrorCode.GENERATION_FAILED,
                trace_id,
                event_id,
                details=[str(e)],
            )

    return EventSourceResponse(event_generator())


@router.post("/index", response_model=IndexResponse)
async def index_documents(
    request: IndexRequest,
) -> IndexResponse:
    """Index documents from a directory.

    Loads documents, splits them into chunks, and stores in vector database.
    """
    indexer = get_indexer()

    # Determine path
    docs_path = Path(request.path) if request.path else rag_settings.docs_path

    if not docs_path.exists():
        raise HTTPException(
            status_code=400,
            detail=f"Documents directory does not exist: {docs_path}",
        )

    try:
        result = indexer.index_documents(
            docs_dir=docs_path,
            clear_existing=request.clear_existing,
        )
    except Exception as e:
        logger.exception(f"Indexing error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

    return IndexResponse(
        indexed_count=result.indexed_count,
        chunk_count=result.chunk_count,
        errors=result.errors,
    )


@router.get("/index/status")
async def get_index_status() -> dict[str, Any]:
    """Get the current index status."""
    indexer = get_indexer()

    return {
        "document_count": indexer.get_document_count(),
        "chroma_dir": str(rag_settings.chroma_path),
        "docs_dir": str(rag_settings.docs_path),
    }


@router.delete("/index")
async def clear_index() -> dict[str, str]:
    """Clear all documents from the index."""
    indexer = get_indexer()
    indexer.clear_index()

    return {"status": "cleared"}


# ============================================================
# Session Management Endpoints
# ============================================================


@router.post("/sessions", response_model=ChatSessionResponse)
async def create_session(
    request: ChatSessionCreate,
    db: DbSession,
) -> ChatSessionResponse:
    """Create a new chat session."""
    repo = ChatRepository(db)
    session = await repo.create_session(title=request.title)
    await db.commit()
    return session_to_response(session)


@router.get("/sessions", response_model=ChatSessionList)
async def list_sessions(
    db: DbSession,
    limit: int = 50,
    offset: int = 0,
) -> ChatSessionList:
    """List all chat sessions."""
    repo = ChatRepository(db)
    sessions = await repo.list_sessions(limit=limit, offset=offset)
    return ChatSessionList(
        sessions=[session_to_response(s) for s in sessions],
        total=len(sessions),
    )


@router.get("/sessions/{session_id}", response_model=ChatSessionWithMessages)
async def get_session(
    session_id: str,
    db: DbSession,
) -> ChatSessionWithMessages:
    """Get a chat session with all messages."""
    try:
        sid = UUID(session_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid session ID format") from e

    repo = ChatRepository(db)
    session = await repo.get_session(sid)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = await repo.get_messages(sid)
    return ChatSessionWithMessages(
        session=session_to_response(session),
        messages=[message_to_response(m) for m in messages],
    )


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    db: DbSession,
) -> dict[str, str]:
    """Delete a chat session and all its messages."""
    try:
        sid = UUID(session_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid session ID format") from e

    repo = ChatRepository(db)
    deleted = await repo.delete_session(sid)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")

    await db.commit()
    return {"status": "deleted"}
