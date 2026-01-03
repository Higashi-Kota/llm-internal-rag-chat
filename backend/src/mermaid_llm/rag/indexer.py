"""Document indexer with ChromaDB vector store."""

# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false
# pyright: reportPrivateUsage=false
# LangChain/Chroma types are not fully annotated

from dataclasses import dataclass, field
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from .config import rag_settings
from .embeddings import get_default_embeddings
from .loaders import load_directory
from .splitter import text_splitter


@dataclass
class IndexResult:
    """Result of document indexing operation."""

    indexed_count: int
    chunk_count: int
    errors: list[str] = field(default_factory=list)


class DocumentIndexer:
    """Handles document indexing and vector store management."""

    def __init__(
        self,
        embeddings: Embeddings | None = None,
        persist_directory: Path | str | None = None,
        collection_name: str = "documents",
    ) -> None:
        """Initialize the document indexer.

        Args:
            embeddings: Embeddings instance. Defaults to configured embeddings.
            persist_directory: ChromaDB persistence directory. Defaults to config.
            collection_name: Name of the Chroma collection.
        """
        self._embeddings = embeddings or get_default_embeddings()
        self._persist_directory = str(persist_directory or rag_settings.chroma_path)
        self._collection_name = collection_name
        self._vector_store: Chroma | None = None

    @property
    def vector_store(self) -> Chroma:
        """Get or create the vector store instance."""
        if self._vector_store is None:
            self._vector_store = Chroma(
                collection_name=self._collection_name,
                embedding_function=self._embeddings,
                persist_directory=self._persist_directory,
            )
        return self._vector_store

    def index_documents(
        self,
        docs_dir: Path | str | None = None,
        clear_existing: bool = False,
    ) -> IndexResult:
        """Index documents from a directory.

        Args:
            docs_dir: Directory containing documents. Defaults to config.
            clear_existing: Whether to clear existing index first.

        Returns:
            IndexResult with statistics.
        """
        if docs_dir is None:
            docs_dir = rag_settings.docs_path
        else:
            docs_dir = Path(docs_dir)

        if clear_existing:
            self.clear_index()

        errors: list[str] = []
        documents: list[Document] = []

        # Load documents
        try:
            for doc in load_directory(docs_dir):
                documents.append(doc)
        except Exception as e:
            errors.append(f"Error loading documents: {e}")

        if not documents:
            return IndexResult(
                indexed_count=0,
                chunk_count=0,
                errors=errors or ["No documents found"],
            )

        # Split documents into chunks
        chunks = text_splitter.split_documents(documents)

        if not chunks:
            return IndexResult(
                indexed_count=len(documents),
                chunk_count=0,
                errors=["No chunks generated after splitting"],
            )

        # Add to vector store
        try:
            self.vector_store.add_documents(chunks)
        except Exception as e:
            errors.append(f"Error adding to vector store: {e}")
            return IndexResult(
                indexed_count=0,
                chunk_count=0,
                errors=errors,
            )

        return IndexResult(
            indexed_count=len(documents),
            chunk_count=len(chunks),
            errors=errors,
        )

    def clear_index(self) -> None:
        """Clear all documents from the index."""
        # Reset the vector store by creating a new collection
        if self._vector_store is not None:
            try:
                # Delete the collection
                self._vector_store.delete_collection()
            except Exception:
                pass
            self._vector_store = None

        # Recreate empty vector store
        _ = self.vector_store

    def get_document_count(self) -> int:
        """Get the number of documents in the index."""
        try:
            collection = self.vector_store._collection
            return collection.count()
        except Exception:
            return 0


# Default indexer instance (lazy initialization)
_default_indexer: DocumentIndexer | None = None


def get_indexer() -> DocumentIndexer:
    """Get the default document indexer instance."""
    global _default_indexer
    if _default_indexer is None:
        _default_indexer = DocumentIndexer()
    return _default_indexer
