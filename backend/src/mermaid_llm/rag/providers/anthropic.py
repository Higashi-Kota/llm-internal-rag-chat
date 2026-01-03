"""Anthropic provider for LLM."""

# pyright: reportCallIssue=false
# LangChain's Pydantic models use dynamic fields that pyright stubs don't capture

from __future__ import annotations

from langchain_anthropic import ChatAnthropic

from ..config import rag_settings
from . import (
    LLMProviderConfig,
    register_llm_provider,
)

# Provider configuration
ANTHROPIC_LLM_CONFIG = LLMProviderConfig(
    name="anthropic",
    default_model="claude-3-haiku-20240307",
    requires_api_key=True,
    api_key_env="ANTHROPIC_API_KEY",
)


def create_anthropic_llm(
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    streaming: bool = True,
) -> ChatAnthropic:
    """Create an Anthropic LLM instance.

    Args:
        model: Model name. Defaults to "claude-3-haiku-20240307".
        temperature: Temperature for generation. Defaults to config value.
        max_tokens: Maximum tokens for generation. Defaults to config value.
        streaming: Whether to enable streaming.

    Returns:
        ChatAnthropic instance.

    Raises:
        ValueError: If ANTHROPIC_API_KEY is not set.
    """
    api_key = rag_settings.anthropic_api_key
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY is required for Anthropic LLM. "
            "Set it in your .env file or environment."
        )
    temp = temperature if temperature is not None else rag_settings.temperature
    return ChatAnthropic(
        anthropic_api_key=api_key,
        model=model or ANTHROPIC_LLM_CONFIG.default_model,
        temperature=temp,
        max_tokens=max_tokens or rag_settings.max_tokens,
        streaming=streaming,
    )


# Register provider (LLM only - Anthropic doesn't provide embeddings)
register_llm_provider(ANTHROPIC_LLM_CONFIG, create_anthropic_llm)
