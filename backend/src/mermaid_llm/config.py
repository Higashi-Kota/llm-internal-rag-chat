"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # OpenAI
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o"

    # Database - use SQLite in mock mode for E2E tests without DB
    database_url: str = ""

    @property
    def effective_database_url(self) -> str:
        """Get effective database URL for asyncpg."""
        if not self.database_url:
            raise ValueError("DATABASE_URL is required.")
        url = self.database_url
        # Convert postgresql:// to postgresql+asyncpg:// for async driver
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        # Parse and transform query parameters for asyncpg compatibility
        parsed = urlparse(url)
        if parsed.query:
            params = parse_qs(parsed.query)
            # Convert sslmode to ssl (Neon uses sslmode, asyncpg uses ssl)
            if "sslmode" in params:
                params["ssl"] = params.pop("sslmode")
            # Remove channel_binding (not supported by asyncpg)
            params.pop("channel_binding", None)
            new_query = urlencode(params, doseq=True)
            parsed = parsed._replace(query=new_query)
            url = urlunparse(parsed)
        return url

    # Application
    debug: bool = False
    use_mock: bool = False

    # CORS - comma-separated list of allowed origins
    cors_origins: str = ""

    @property
    def is_mock_mode(self) -> bool:
        """Check if mock mode is enabled (no API key or explicit mock flag)."""
        return self.use_mock or not self.openai_api_key

    @property
    def allowed_origins(self) -> list[str]:
        """Get list of allowed CORS origins."""
        # Default origins for local development
        default_origins = [
            "http://localhost:5175",
            "http://localhost:5173",
            "http://127.0.0.1:5175",
            "http://127.0.0.1:5173",
        ]
        # Add configured origins
        if self.cors_origins:
            extra = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
            return default_origins + extra
        return default_origins


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
