"""RAG chain using LangGraph."""

# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false
# pyright: reportMissingTypeStubs=false
# pyright: reportMissingTypeArgument=false
# pyright: reportUnknownParameterType=false
# LangChain/LangGraph types are not fully annotated

from collections.abc import AsyncIterator
from typing import Any

from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from .nodes.generate import generate, generate_streaming
from .nodes.retrieve import retrieve
from .state import RAGState


def build_rag_graph() -> CompiledStateGraph:
    """Build the RAG graph.

    Graph structure:
        START -> retrieve -> generate -> END

    Returns:
        Compiled LangGraph for RAG.
    """
    graph = StateGraph(RAGState)

    # Add nodes
    graph.add_node("retrieve", retrieve)
    graph.add_node("generate", generate)

    # Add edges
    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)

    return graph.compile()


# Compiled graph instance
rag_graph = build_rag_graph()


async def run_rag(
    query: str,
    chat_history: list[dict[str, str]] | None = None,
) -> RAGState:
    """Run the RAG chain.

    Args:
        query: User query.
        chat_history: Previous chat messages as list of {"role": str, "content": str}.

    Returns:
        Final RAG state with response.
    """
    # Convert chat history to messages
    messages = []
    if chat_history:
        for msg in chat_history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                from langchain_core.messages import AIMessage

                messages.append(AIMessage(content=msg["content"]))

    # Add current query
    messages.append(HumanMessage(content=query))

    # Initial state
    initial_state: RAGState = {
        "messages": messages,
        "query": query,
        "retrieved_docs": [],
        "context": "",
        "sources": [],
        "response": "",
        "is_streaming": False,
        "model": "",
        "provider": "",
    }

    # Run graph
    result = await rag_graph.ainvoke(initial_state)
    return result  # type: ignore[return-value]


async def stream_rag(
    query: str,
    chat_history: list[dict[str, str]] | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """Stream the RAG chain response.

    Args:
        query: User query.
        chat_history: Previous chat messages.

    Yields:
        State updates from the graph.
    """
    # Convert chat history to messages
    messages = []
    if chat_history:
        for msg in chat_history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                from langchain_core.messages import AIMessage

                messages.append(AIMessage(content=msg["content"]))

    # Add current query
    messages.append(HumanMessage(content=query))

    # Initial state
    initial_state: RAGState = {
        "messages": messages,
        "query": query,
        "retrieved_docs": [],
        "context": "",
        "sources": [],
        "response": "",
        "is_streaming": True,
        "model": "",
        "provider": "",
    }

    # First, run retrieval
    from .retriever import get_retriever

    retriever = get_retriever()
    result = await retriever.aretrieve(query)

    # Yield retrieval result
    yield {
        "event": "sources",
        "sources": result.sources,
        "context": result.context,
    }

    # Update state with retrieval results
    state = {
        **initial_state,
        "retrieved_docs": result.documents,
        "context": result.context,
        "sources": result.sources,
    }

    # Stream generation
    async for update in generate_streaming(state):  # type: ignore[arg-type]
        yield {
            "event": "chunk",
            "response": update.get("response", ""),
            "is_streaming": update.get("is_streaming", True),
        }

    # Final update with metadata
    yield {
        "event": "done",
        "response": update.get("response", ""),  # type: ignore[possibly-undefined]
        "model": update.get("model", ""),  # type: ignore[possibly-undefined]
        "provider": update.get("provider", ""),  # type: ignore[possibly-undefined]
        "sources": result.sources,
    }
