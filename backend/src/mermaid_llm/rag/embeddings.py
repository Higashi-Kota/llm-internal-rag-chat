"""Embedding model factory using provider registry.

This module provides a unified interface for creating embedding instances
from any registered provider. Provider switching is done via the
EMBEDDING_PROVIDER environment variable.
"""

from __future__ import annotations

from langchain_core.embeddings import Embeddings

from .config import rag_settings
from .providers import get_embedding_provider


def create_embeddings(
    provider: str | None = None,
    model: str | None = None,
) -> Embeddings:
    """Create an embeddings instance based on provider.

    This factory function delegates to the appropriate provider factory
    based on the provider name. Providers are registered in the providers
    subpackage.

    Args:
        provider: Embedding provider name. Defaults to EMBEDDING_PROVIDER env var.
        model: Model name. Defaults to provider's default or config value.

    Returns:
        Embeddings instance from the specified provider.

    Raises:
        ValueError: If provider is not registered.

    Example:
        # Use default provider (from EMBEDDING_PROVIDER env var)
        embeddings = create_embeddings()

        # Use specific provider
        embeddings = create_embeddings(provider="openai")
    """
    provider_name = provider or rag_settings.embedding_provider
    _config, factory = get_embedding_provider(provider_name)

    return factory(model=model)


def get_default_embeddings() -> Embeddings:
    """Get embeddings instance with default configuration.

    This is a convenience function that creates embeddings using the default
    provider and settings from environment variables.

    Returns:
        Embeddings instance with default configuration.
    """
    return create_embeddings()
