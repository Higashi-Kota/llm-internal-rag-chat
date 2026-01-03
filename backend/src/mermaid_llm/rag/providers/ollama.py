"""Ollama provider for local LLM and embeddings.

This is the default provider for local development, using Ollama
running on localhost.
"""

from __future__ import annotations

from langchain_ollama import ChatOllama, OllamaEmbeddings

from ..config import rag_settings
from . import (
    EmbeddingProviderConfig,
    LLMProviderConfig,
    register_embedding_provider,
    register_llm_provider,
)

# Provider configurations
OLLAMA_LLM_CONFIG = LLMProviderConfig(
    name="ollama",
    default_model="gemma3:4b",
    requires_api_key=False,
    api_key_env=None,
)

OLLAMA_EMBEDDING_CONFIG = EmbeddingProviderConfig(
    name="ollama",
    default_model="nomic-embed-text",
    requires_api_key=False,
    api_key_env=None,
)


def create_ollama_llm(
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    streaming: bool = True,  # noqa: ARG001
) -> ChatOllama:
    """Create an Ollama LLM instance.

    Args:
        model: Model name. Defaults to config value or "gemma3:4b".
        temperature: Temperature for generation. Defaults to config value.
        max_tokens: Maximum tokens for generation. Defaults to config value.
        streaming: Whether to enable streaming (ignored for Ollama, always streams).

    Returns:
        ChatOllama instance.
    """
    temp = temperature if temperature is not None else rag_settings.temperature
    return ChatOllama(
        base_url=rag_settings.ollama_base_url,
        model=model or rag_settings.llm_model or OLLAMA_LLM_CONFIG.default_model,
        temperature=temp,
        num_predict=max_tokens or rag_settings.max_tokens,
    )


def create_ollama_embeddings(
    model: str | None = None,
) -> OllamaEmbeddings:
    """Create an Ollama embeddings instance.

    Args:
        model: Model name. Defaults to config value or "nomic-embed-text".

    Returns:
        OllamaEmbeddings instance.
    """
    model_name = (
        model or rag_settings.embedding_model or OLLAMA_EMBEDDING_CONFIG.default_model
    )
    return OllamaEmbeddings(
        base_url=rag_settings.ollama_base_url,
        model=model_name,
    )


# Register providers
register_llm_provider(OLLAMA_LLM_CONFIG, create_ollama_llm)
register_embedding_provider(OLLAMA_EMBEDDING_CONFIG, create_ollama_embeddings)
