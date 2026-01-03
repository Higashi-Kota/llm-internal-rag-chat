"""LLM factory using provider registry.

This module provides a unified interface for creating LLM instances
from any registered provider. Provider switching is done via the
LLM_PROVIDER environment variable.
"""

from __future__ import annotations

from langchain_core.language_models import BaseChatModel

from .config import rag_settings
from .providers import get_llm_provider


def create_llm(
    provider: str | None = None,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    streaming: bool = True,
) -> BaseChatModel:
    """Create an LLM instance based on provider.

    This factory function delegates to the appropriate provider factory
    based on the provider name. Providers are registered in the providers
    subpackage.

    Args:
        provider: LLM provider name. Defaults to LLM_PROVIDER env var.
        model: Model name. Defaults to provider's default or config value.
        temperature: Temperature for generation. Defaults to config value.
        max_tokens: Maximum tokens for generation. Defaults to config value.
        streaming: Whether to enable streaming.

    Returns:
        BaseChatModel instance from the specified provider.

    Raises:
        ValueError: If provider is not registered.

    Example:
        # Use default provider (from LLM_PROVIDER env var)
        llm = create_llm()

        # Use specific provider
        llm = create_llm(provider="openai", model="gpt-4o")

        # Override settings
        llm = create_llm(temperature=0.5, max_tokens=1000)
    """
    provider_name = provider or rag_settings.llm_provider
    _config, factory = get_llm_provider(provider_name)

    return factory(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        streaming=streaming,
    )


def get_default_llm(streaming: bool = True) -> BaseChatModel:
    """Get LLM instance with default configuration.

    This is a convenience function that creates an LLM using the default
    provider and settings from environment variables.

    Args:
        streaming: Whether to enable streaming.

    Returns:
        BaseChatModel instance with default configuration.
    """
    return create_llm(streaming=streaming)
