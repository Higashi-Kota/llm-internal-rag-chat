"""RAG (Retrieval-Augmented Generation) module."""

# pyright: reportUnknownVariableType=false

from .chain import rag_graph, run_rag, stream_rag
from .config import RAGSettings, get_rag_settings, rag_settings
from .indexer import DocumentIndexer, IndexResult, get_indexer
from .retriever import DocumentRetriever, RetrievalResult, SourceInfo, get_retriever

__all__ = [
    # Chain
    "rag_graph",
    "run_rag",
    "stream_rag",
    # Config
    "RAGSettings",
    "get_rag_settings",
    "rag_settings",
    # Indexer
    "DocumentIndexer",
    "IndexResult",
    "get_indexer",
    # Retriever
    "DocumentRetriever",
    "RetrievalResult",
    "SourceInfo",
    "get_retriever",
]
