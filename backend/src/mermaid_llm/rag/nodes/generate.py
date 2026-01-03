"""Generate node for RAG graph."""

# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnnecessaryIsInstance=false
# LangChain types are not fully annotated

from typing import Any

from langchain_core.messages import AIMessage

from ..config import rag_settings
from ..llm import get_default_llm
from ..prompts import rag_prompt
from ..state import RAGState


async def generate(state: RAGState) -> dict[str, Any]:
    """Generate response using retrieved context.

    Args:
        state: Current RAG state.

    Returns:
        Dict with generated response.
    """
    context = state["context"]
    messages = state["messages"]

    # Create prompt with context
    prompt = rag_prompt.format_messages(
        context=context,
        messages=messages,
    )

    # Get LLM
    llm = get_default_llm(streaming=False)

    # Generate response
    response = await llm.ainvoke(prompt)

    # Extract content
    content = ""
    if isinstance(response.content, str):
        content = response.content
    elif isinstance(response.content, list):
        content = "".join(
            chunk if isinstance(chunk, str) else chunk.get("text", "")
            for chunk in response.content
        )

    return {
        "response": content,
        "model": rag_settings.llm_model,
        "provider": rag_settings.llm_provider,
    }


async def generate_streaming(state: RAGState):
    """Generate response with streaming.

    This is a generator that yields partial responses.

    Args:
        state: Current RAG state.

    Yields:
        Dict with partial response updates.
    """
    context = state["context"]
    messages = state["messages"]

    # Create prompt with context
    prompt = rag_prompt.format_messages(
        context=context,
        messages=messages,
    )

    # Get LLM with streaming
    llm = get_default_llm(streaming=True)

    # Stream response
    accumulated = ""
    async for chunk in llm.astream(prompt):
        if isinstance(chunk, AIMessage) and chunk.content:
            content = ""
            if isinstance(chunk.content, str):
                content = chunk.content
            elif isinstance(chunk.content, list):
                content = "".join(
                    c if isinstance(c, str) else c.get("text", "")
                    for c in chunk.content
                )
            accumulated += content
            yield {
                "response": accumulated,
                "is_streaming": True,
            }

    # Final update
    yield {
        "response": accumulated,
        "is_streaming": False,
        "model": rag_settings.llm_model,
        "provider": rag_settings.llm_provider,
    }
