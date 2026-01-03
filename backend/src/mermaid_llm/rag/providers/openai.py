"""OpenAI provider for LLM and embeddings."""

# pyright: reportCallIssue=false
# LangChain's Pydantic models use dynamic fields that pyright stubs don't capture

from __future__ import annotations

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from ..config import rag_settings
from . import (
    EmbeddingProviderConfig,
    LLMProviderConfig,
    register_embedding_provider,
    register_llm_provider,
)

# Provider configurations
OPENAI_LLM_CONFIG = LLMProviderConfig(
    name="openai",
    default_model="gpt-4o-mini",
    requires_api_key=True,
    api_key_env="OPENAI_API_KEY",
)

OPENAI_EMBEDDING_CONFIG = EmbeddingProviderConfig(
    name="openai",
    default_model="text-embedding-3-small",
    requires_api_key=True,
    api_key_env="OPENAI_API_KEY",
)


def create_openai_llm(
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    streaming: bool = True,
) -> ChatOpenAI:
    """Create an OpenAI LLM instance.

    Args:
        model: Model name. Defaults to "gpt-4o-mini".
        temperature: Temperature for generation. Defaults to config value.
        max_tokens: Maximum tokens for generation. Defaults to config value.
        streaming: Whether to enable streaming.

    Returns:
        ChatOpenAI instance.

    Raises:
        ValueError: If OPENAI_API_KEY is not set.
    """
    api_key = rag_settings.openai_api_key
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY is required for OpenAI LLM. "
            "Set it in your .env file or environment."
        )
    temp = temperature if temperature is not None else rag_settings.temperature
    return ChatOpenAI(
        openai_api_key=api_key,
        model=model or OPENAI_LLM_CONFIG.default_model,
        temperature=temp,
        max_tokens=max_tokens or rag_settings.max_tokens,
        streaming=streaming,
    )


def create_openai_embeddings(
    model: str | None = None,
) -> OpenAIEmbeddings:
    """Create an OpenAI embeddings instance.

    Args:
        model: Model name. Defaults to "text-embedding-3-small".

    Returns:
        OpenAIEmbeddings instance.

    Raises:
        ValueError: If OPENAI_API_KEY is not set.
    """
    api_key = rag_settings.openai_api_key
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY is required for OpenAI embeddings. "
            "Set it in your .env file or environment."
        )
    return OpenAIEmbeddings(
        openai_api_key=api_key,
        model=model or OPENAI_EMBEDDING_CONFIG.default_model,
    )


# Register providers
register_llm_provider(OPENAI_LLM_CONFIG, create_openai_llm)
register_embedding_provider(OPENAI_EMBEDDING_CONFIG, create_openai_embeddings)
