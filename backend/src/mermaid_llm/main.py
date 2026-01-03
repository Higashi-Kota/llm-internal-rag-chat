"""FastAPI application entry point."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mermaid_llm.api.routers import rag
from mermaid_llm.config import settings
from mermaid_llm.rag import rag_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

app = FastAPI(
    title="RAG Chat API",
    version="0.0.1",
    description="Local RAG system with LangChain + Ollama + ChromaDB",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(rag.router)


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "ok",
        "mode": "mock" if settings.is_mock_mode else "live",
        "llm_provider": rag_settings.llm_provider,
        "llm_model": rag_settings.llm_model,
    }


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "RAG Chat API", "docs": "/docs"}
