"""Google Gemini provider for LLM."""

from __future__ import annotations

from langchain_google_genai import ChatGoogleGenerativeAI

from ..config import rag_settings
from . import (
    LLMProviderConfig,
    register_llm_provider,
)

# Provider configuration
GEMINI_LLM_CONFIG = LLMProviderConfig(
    name="gemini",
    default_model="gemini-1.5-flash",
    requires_api_key=True,
    api_key_env="GEMINI_API_KEY",
)


def create_gemini_llm(
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    streaming: bool = True,  # noqa: ARG001
) -> ChatGoogleGenerativeAI:
    """Create a Gemini LLM instance.

    Args:
        model: Model name. Defaults to "gemini-1.5-flash".
        temperature: Temperature for generation. Defaults to config value.
        max_tokens: Maximum tokens for generation. Defaults to config value.
        streaming: Whether to enable streaming (handled differently by Gemini).

    Returns:
        ChatGoogleGenerativeAI instance.

    Raises:
        ValueError: If GEMINI_API_KEY is not set.
    """
    api_key = rag_settings.gemini_api_key
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is required for Gemini LLM. "
            "Set it in your .env file or environment."
        )
    temp = temperature if temperature is not None else rag_settings.temperature
    return ChatGoogleGenerativeAI(
        google_api_key=api_key,
        model=model or GEMINI_LLM_CONFIG.default_model,
        temperature=temp,
        max_output_tokens=max_tokens or rag_settings.max_tokens,
    )


# Register provider (LLM only - Gemini embeddings require different setup)
register_llm_provider(GEMINI_LLM_CONFIG, create_gemini_llm)
