"""RAG graph state definition."""

from typing import TypedDict

from langchain_core.documents import Document
from langchain_core.messages import BaseMessage

from .retriever import SourceInfo


class RAGState(TypedDict):
    """State for the RAG chain graph."""

    # Input
    messages: list[BaseMessage]  # Chat history
    query: str  # Current user query

    # Retrieval
    retrieved_docs: list[Document]  # Retrieved context documents
    context: str  # Combined context text
    sources: list[SourceInfo]  # Source document info

    # Generation
    response: str  # Generated response (accumulated)
    is_streaming: bool  # Whether currently streaming

    # Metadata
    model: str  # Model used for generation
    provider: str  # Provider used
