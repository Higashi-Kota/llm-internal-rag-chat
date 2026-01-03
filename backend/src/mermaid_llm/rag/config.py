"""RAG-specific configuration."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class RAGSettings(BaseSettings):
    """RAG-specific settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Ollama settings
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "gemma3:4b"
    embedding_model: str = "nomic-embed-text"

    # Provider selection
    llm_provider: Literal["ollama", "openai", "anthropic", "gemini"] = "ollama"
    embedding_provider: Literal["ollama", "openai"] = "ollama"

    # Cloud API keys (optional - fallback to main settings)
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    gemini_api_key: str | None = None

    # Paths
    chroma_dir: str = "data/chroma"
    docs_dir: str = "data/docs"

    # Chunking parameters
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # Retrieval parameters
    retrieval_k: int = 4

    # LLM parameters
    max_tokens: int = 2048
    temperature: float = 0.7

    @property
    def chroma_path(self) -> Path:
        """Get ChromaDB directory as Path."""
        return Path(self.chroma_dir)

    @property
    def docs_path(self) -> Path:
        """Get documents directory as Path."""
        return Path(self.docs_dir)


@lru_cache
def get_rag_settings() -> RAGSettings:
    """Get cached RAG settings instance."""
    return RAGSettings()


rag_settings = get_rag_settings()
