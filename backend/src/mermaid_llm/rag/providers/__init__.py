"""Provider registry for LLM and Embedding models.

This module provides a registry pattern for managing LLM and embedding providers.
Each provider registers itself with the registry, allowing clean separation of
provider-specific code and easy switching via environment variables.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from langchain_core.embeddings import Embeddings
    from langchain_core.language_models import BaseChatModel


@dataclass(frozen=True)
class LLMProviderConfig:
    """Configuration for an LLM provider."""

    name: str
    default_model: str
    requires_api_key: bool = True
    api_key_env: str | None = None


@dataclass(frozen=True)
class EmbeddingProviderConfig:
    """Configuration for an embedding provider."""

    name: str
    default_model: str
    requires_api_key: bool = True
    api_key_env: str | None = None


# Type aliases for factory functions
LLMFactory = Callable[..., "BaseChatModel"]
EmbeddingFactory = Callable[..., "Embeddings"]

# Provider registries
_llm_registry: dict[str, tuple[LLMProviderConfig, LLMFactory]] = {}
_embedding_registry: dict[str, tuple[EmbeddingProviderConfig, EmbeddingFactory]] = {}


def register_llm_provider(config: LLMProviderConfig, factory: LLMFactory) -> None:
    """Register an LLM provider.

    Args:
        config: Provider configuration.
        factory: Factory function that creates LLM instances.
    """
    _llm_registry[config.name] = (config, factory)


def register_embedding_provider(
    config: EmbeddingProviderConfig, factory: EmbeddingFactory
) -> None:
    """Register an embedding provider.

    Args:
        config: Provider configuration.
        factory: Factory function that creates embedding instances.
    """
    _embedding_registry[config.name] = (config, factory)


def get_llm_provider(name: str) -> tuple[LLMProviderConfig, LLMFactory]:
    """Get an LLM provider by name.

    Args:
        name: Provider name (e.g., "ollama", "openai").

    Returns:
        Tuple of (config, factory).

    Raises:
        ValueError: If provider is not registered.
    """
    if name not in _llm_registry:
        available = ", ".join(_llm_registry.keys())
        raise ValueError(f"Unknown LLM provider: {name}. Available: {available}")
    return _llm_registry[name]


def get_embedding_provider(
    name: str,
) -> tuple[EmbeddingProviderConfig, EmbeddingFactory]:
    """Get an embedding provider by name.

    Args:
        name: Provider name (e.g., "ollama", "openai").

    Returns:
        Tuple of (config, factory).

    Raises:
        ValueError: If provider is not registered.
    """
    if name not in _embedding_registry:
        available = ", ".join(_embedding_registry.keys())
        raise ValueError(f"Unknown embedding provider: {name}. Available: {available}")
    return _embedding_registry[name]


def list_llm_providers() -> list[str]:
    """List all registered LLM provider names."""
    return list(_llm_registry.keys())


def list_embedding_providers() -> list[str]:
    """List all registered embedding provider names."""
    return list(_embedding_registry.keys())


# Import providers to trigger registration
# pyright: reportUnusedImport=false
from . import anthropic as _anthropic  # noqa: E402, F401
from . import gemini as _gemini  # noqa: E402, F401
from . import ollama as _ollama  # noqa: E402, F401
from . import openai as _openai  # noqa: E402, F401

del _anthropic, _gemini, _ollama, _openai  # Avoid "unused import" warnings

__all__ = [
    "LLMProviderConfig",
    "EmbeddingProviderConfig",
    "LLMFactory",
    "EmbeddingFactory",
    "register_llm_provider",
    "register_embedding_provider",
    "get_llm_provider",
    "get_embedding_provider",
    "list_llm_providers",
    "list_embedding_providers",
]
