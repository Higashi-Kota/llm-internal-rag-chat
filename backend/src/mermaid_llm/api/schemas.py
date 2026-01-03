"""Pydantic schemas for API requests and responses."""

from pydantic import BaseModel, Field


class DiagramRequest(BaseModel):
    """Request schema for diagram generation."""

    prompt: str = Field(..., min_length=1, description="Prompt describing the diagram")
    language_hint: str | None = Field(
        default=None, description="Language hint: null/auto, ja, or en"
    )
    diagram_type_hint: str | None = Field(
        default=None,
        description=(
            "Diagram type hint: null/auto, flowchart, sequence, "
            "gantt, class, er, state, journey"
        ),
    )


class DiagramMeta(BaseModel):
    """Metadata for diagram generation."""

    model: str
    latency_ms: int
    attempts: int
    trace_id: str | None = None


class DiagramResponse(BaseModel):
    """Response schema for diagram generation."""

    mermaid_code: str
    diagram_type: str
    language: str
    errors: list[str]
    meta: DiagramMeta


class SSEMetaEvent(BaseModel):
    """SSE meta event data."""

    trace_id: str
    model: str
    diagram_type: str
    language: str


class SSEChunkEvent(BaseModel):
    """SSE chunk event data."""

    text: str


class SSEErrorEvent(BaseModel):
    """SSE error event data."""

    code: str
    category: str
    message: str
    details: list[str] | None = None
    trace_id: str
    retryable: bool = True


# ============================================================
# RAG Schemas
# ============================================================


class MessageInput(BaseModel):
    """Input message for chat."""

    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1)


class RAGChatRequest(BaseModel):
    """Request schema for RAG chat."""

    messages: list[MessageInput] = Field(..., min_length=1)
    session_id: str | None = Field(default=None, description="Optional session ID")


class SourceInfoResponse(BaseModel):
    """Source document information."""

    filename: str
    page: int | None = None
    slide: int | None = None
    sheet: str | None = None
    score: float = 0.0


class RAGChatResponse(BaseModel):
    """Response schema for RAG chat (non-streaming)."""

    response: str
    sources: list[SourceInfoResponse]
    model: str
    provider: str
    session_id: str | None = None


class IndexRequest(BaseModel):
    """Request schema for document indexing."""

    path: str | None = Field(default=None, description="Path to documents directory")
    clear_existing: bool = Field(default=False, description="Clear existing index")


class IndexResponse(BaseModel):
    """Response schema for document indexing."""

    indexed_count: int
    chunk_count: int
    errors: list[str]


# RAG SSE Events
class SSERAGMetaEvent(BaseModel):
    """SSE meta event for RAG chat."""

    trace_id: str
    model: str
    provider: str
    session_id: str | None = None


class SSERAGSourcesEvent(BaseModel):
    """SSE sources event for RAG chat."""

    sources: list[SourceInfoResponse]


class SSERAGChunkEvent(BaseModel):
    """SSE chunk event for RAG chat."""

    text: str


class SSERAGDoneEvent(BaseModel):
    """SSE done event for RAG chat."""

    response: str
    sources: list[SourceInfoResponse]
    model: str
    provider: str


# ============================================================
# Chat Session Schemas
# ============================================================


class ChatSessionCreate(BaseModel):
    """Request schema for creating a chat session."""

    title: str | None = Field(default=None, description="Optional session title")


class ChatSessionResponse(BaseModel):
    """Response schema for a chat session."""

    id: str
    title: str | None
    created_at: str
    updated_at: str


class ChatMessageResponse(BaseModel):
    """Response schema for a chat message."""

    id: str
    role: str
    content: str
    sources: list[SourceInfoResponse] | None = None
    model: str | None = None
    provider: str | None = None
    created_at: str


class ChatSessionWithMessages(BaseModel):
    """Response schema for session with messages."""

    session: ChatSessionResponse
    messages: list[ChatMessageResponse]


class ChatSessionList(BaseModel):
    """Response schema for listing sessions."""

    sessions: list[ChatSessionResponse]
    total: int
