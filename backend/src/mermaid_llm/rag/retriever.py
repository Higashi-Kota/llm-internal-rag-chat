"""Document retriever for similarity search."""

# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false
# LangChain Document.metadata type is not fully annotated

from dataclasses import dataclass

from langchain_core.documents import Document

from .config import rag_settings
from .indexer import get_indexer


@dataclass
class SourceInfo:
    """Information about a source document."""

    filename: str
    page: int | None = None
    slide: int | None = None
    sheet: str | None = None
    score: float = 0.0

    @classmethod
    def from_document(cls, doc: Document, score: float = 0.0) -> "SourceInfo":
        """Create SourceInfo from a Document."""
        metadata = doc.metadata
        return cls(
            filename=metadata.get("filename", "unknown"),
            page=metadata.get("page"),
            slide=metadata.get("slide"),
            sheet=metadata.get("sheet"),
            score=score,
        )


@dataclass
class RetrievalResult:
    """Result of a retrieval operation."""

    documents: list[Document]
    sources: list[SourceInfo]

    @property
    def context(self) -> str:
        """Get combined context from all documents."""
        return "\n\n---\n\n".join(doc.page_content for doc in self.documents)


class DocumentRetriever:
    """Handles document retrieval from vector store."""

    def __init__(self, k: int | None = None) -> None:
        """Initialize the retriever.

        Args:
            k: Number of documents to retrieve. Defaults to config value.
        """
        self._k = k or rag_settings.retrieval_k
        self._indexer = get_indexer()

    def retrieve(
        self,
        query: str,
        k: int | None = None,
    ) -> RetrievalResult:
        """Retrieve documents similar to the query.

        Args:
            query: Search query.
            k: Number of documents to retrieve. Overrides default.

        Returns:
            RetrievalResult with documents and source info.
        """
        k = k or self._k
        vector_store = self._indexer.vector_store

        # Perform similarity search with scores
        results = vector_store.similarity_search_with_score(query, k=k)

        documents = []
        sources = []
        seen_sources: set[str] = set()

        for doc, score in results:
            documents.append(doc)
            # Create source info (deduplicate by filename+page/slide/sheet)
            source = SourceInfo.from_document(doc, score=float(score))
            source_key = (
                f"{source.filename}:{source.page}:{source.slide}:{source.sheet}"
            )
            if source_key not in seen_sources:
                sources.append(source)
                seen_sources.add(source_key)

        return RetrievalResult(documents=documents, sources=sources)

    async def aretrieve(
        self,
        query: str,
        k: int | None = None,
    ) -> RetrievalResult:
        """Async version of retrieve.

        Note: ChromaDB operations are sync, but this provides async interface
        for consistency with LangGraph async patterns.
        """
        # ChromaDB is sync, so we just call the sync version
        # In production, you might want to use asyncio.to_thread
        return self.retrieve(query, k)


# Default retriever instance (lazy initialization)
_default_retriever: DocumentRetriever | None = None


def get_retriever() -> DocumentRetriever:
    """Get the default document retriever instance."""
    global _default_retriever
    if _default_retriever is None:
        _default_retriever = DocumentRetriever()
    return _default_retriever
