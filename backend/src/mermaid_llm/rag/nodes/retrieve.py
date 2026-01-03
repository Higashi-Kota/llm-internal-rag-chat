"""Retrieve node for RAG graph."""

from typing import Any

from ..retriever import get_retriever
from ..state import RAGState


async def retrieve(state: RAGState) -> dict[str, Any]:
    """Retrieve relevant documents from vector store.

    Args:
        state: Current RAG state.

    Returns:
        Dict with retrieved documents, context, and sources.
    """
    query = state["query"]
    retriever = get_retriever()

    result = await retriever.aretrieve(query)

    return {
        "retrieved_docs": result.documents,
        "context": result.context,
        "sources": result.sources,
    }
