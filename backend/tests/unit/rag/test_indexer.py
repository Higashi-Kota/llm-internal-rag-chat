"""Tests for document indexer."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from langchain_core.documents import Document

from mermaid_llm.rag.indexer import (
    DocumentIndexer,
    IndexResult,
    get_indexer,
)


class TestIndexResult:
    """Tests for IndexResult dataclass."""

    def test_default_errors(self):
        """Test IndexResult has empty errors by default."""
        result = IndexResult(indexed_count=5, chunk_count=10)
        assert result.errors == []

    def test_with_errors(self):
        """Test IndexResult with errors."""
        result = IndexResult(
            indexed_count=0,
            chunk_count=0,
            errors=["Error 1", "Error 2"],
        )
        assert len(result.errors) == 2
        assert "Error 1" in result.errors


class TestDocumentIndexer:
    """Tests for DocumentIndexer class."""

    def test_init_default_embeddings(self):
        """Test indexer uses default embeddings when not provided."""
        with patch("mermaid_llm.rag.indexer.get_default_embeddings") as mock_embed:
            mock_embeddings = MagicMock()
            mock_embed.return_value = mock_embeddings

            with patch("mermaid_llm.rag.indexer.rag_settings") as mock_settings:
                mock_settings.chroma_path = Path("/tmp/chroma")

                indexer = DocumentIndexer()

                mock_embed.assert_called_once()
                assert indexer._embeddings == mock_embeddings

    def test_init_custom_embeddings(self):
        """Test indexer uses custom embeddings when provided."""
        custom_embeddings = MagicMock()

        with patch("mermaid_llm.rag.indexer.rag_settings") as mock_settings:
            mock_settings.chroma_path = Path("/tmp/chroma")

            indexer = DocumentIndexer(embeddings=custom_embeddings)

            assert indexer._embeddings == custom_embeddings

    def test_init_custom_persist_directory(self):
        """Test indexer uses custom persist directory."""
        with patch("mermaid_llm.rag.indexer.get_default_embeddings"):
            indexer = DocumentIndexer(persist_directory="/custom/path")

            assert indexer._persist_directory == "/custom/path"

    def test_init_custom_collection_name(self):
        """Test indexer uses custom collection name."""
        with patch("mermaid_llm.rag.indexer.get_default_embeddings"):
            with patch("mermaid_llm.rag.indexer.rag_settings") as mock_settings:
                mock_settings.chroma_path = Path("/tmp/chroma")

                indexer = DocumentIndexer(collection_name="custom_collection")

                assert indexer._collection_name == "custom_collection"

    def test_vector_store_lazy_init(self):
        """Test vector store is lazily initialized."""
        with patch("mermaid_llm.rag.indexer.get_default_embeddings"):
            with patch("mermaid_llm.rag.indexer.rag_settings") as mock_settings:
                mock_settings.chroma_path = Path("/tmp/chroma")

                indexer = DocumentIndexer()

                assert indexer._vector_store is None

    def test_vector_store_property(self):
        """Test vector store property creates Chroma instance."""
        mock_embeddings = MagicMock()

        with patch(
            "mermaid_llm.rag.indexer.get_default_embeddings",
            return_value=mock_embeddings,
        ):
            with patch("mermaid_llm.rag.indexer.rag_settings") as mock_settings:
                mock_settings.chroma_path = Path("/tmp/chroma")

                with patch("mermaid_llm.rag.indexer.Chroma") as mock_chroma:
                    mock_store = MagicMock()
                    mock_chroma.return_value = mock_store

                    indexer = DocumentIndexer()
                    store = indexer.vector_store

                    mock_chroma.assert_called_once_with(
                        collection_name="documents",
                        embedding_function=mock_embeddings,
                        persist_directory="/tmp/chroma",
                    )
                    assert store == mock_store

    def test_index_documents_no_documents(self, tmp_path: Path):
        """Test indexing empty directory."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        with patch("mermaid_llm.rag.indexer.get_default_embeddings"):
            with patch("mermaid_llm.rag.indexer.rag_settings") as mock_settings:
                mock_settings.chroma_path = tmp_path / "chroma"
                mock_settings.docs_path = docs_dir

                with patch(
                    "mermaid_llm.rag.indexer.load_directory", return_value=iter([])
                ):
                    indexer = DocumentIndexer()
                    result = indexer.index_documents(docs_dir)

                    assert result.indexed_count == 0
                    assert result.chunk_count == 0
                    assert "No documents found" in result.errors

    def test_index_documents_success(self, tmp_path: Path):
        """Test successful document indexing."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        mock_docs = [
            Document(page_content="Content 1", metadata={"source": "file1.txt"}),
            Document(page_content="Content 2", metadata={"source": "file2.txt"}),
        ]

        mock_chunks = [
            Document(page_content="Chunk 1", metadata={}),
            Document(page_content="Chunk 2", metadata={}),
            Document(page_content="Chunk 3", metadata={}),
        ]

        with patch("mermaid_llm.rag.indexer.get_default_embeddings"):
            with patch("mermaid_llm.rag.indexer.rag_settings") as mock_settings:
                mock_settings.chroma_path = tmp_path / "chroma"
                mock_settings.docs_path = docs_dir

                with patch(
                    "mermaid_llm.rag.indexer.load_directory",
                    return_value=iter(mock_docs),
                ):
                    with patch(
                        "mermaid_llm.rag.indexer.text_splitter"
                    ) as mock_splitter:
                        mock_splitter.split_documents.return_value = mock_chunks

                        with patch("mermaid_llm.rag.indexer.Chroma") as mock_chroma:
                            mock_store = MagicMock()
                            mock_chroma.return_value = mock_store

                            indexer = DocumentIndexer()
                            result = indexer.index_documents(docs_dir)

                            assert result.indexed_count == 2
                            assert result.chunk_count == 3
                            assert len(result.errors) == 0
                            mock_store.add_documents.assert_called_once_with(
                                mock_chunks
                            )

    def test_index_documents_clear_existing(self, tmp_path: Path):
        """Test indexing with clear_existing flag."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        with patch("mermaid_llm.rag.indexer.get_default_embeddings"):
            with patch("mermaid_llm.rag.indexer.rag_settings") as mock_settings:
                mock_settings.chroma_path = tmp_path / "chroma"
                mock_settings.docs_path = docs_dir

                with patch(
                    "mermaid_llm.rag.indexer.load_directory", return_value=iter([])
                ):
                    indexer = DocumentIndexer()
                    indexer.clear_index = MagicMock()

                    indexer.index_documents(docs_dir, clear_existing=True)

                    indexer.clear_index.assert_called_once()

    def test_index_documents_vector_store_error(self, tmp_path: Path):
        """Test handling of vector store errors."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        mock_docs = [Document(page_content="Content", metadata={})]
        mock_chunks = [Document(page_content="Chunk", metadata={})]

        with patch("mermaid_llm.rag.indexer.get_default_embeddings"):
            with patch("mermaid_llm.rag.indexer.rag_settings") as mock_settings:
                mock_settings.chroma_path = tmp_path / "chroma"
                mock_settings.docs_path = docs_dir

                with patch(
                    "mermaid_llm.rag.indexer.load_directory",
                    return_value=iter(mock_docs),
                ):
                    with patch(
                        "mermaid_llm.rag.indexer.text_splitter"
                    ) as mock_splitter:
                        mock_splitter.split_documents.return_value = mock_chunks

                        with patch("mermaid_llm.rag.indexer.Chroma") as mock_chroma:
                            mock_store = MagicMock()
                            mock_store.add_documents.side_effect = Exception(
                                "Store error"
                            )
                            mock_chroma.return_value = mock_store

                            indexer = DocumentIndexer()
                            result = indexer.index_documents(docs_dir)

                            assert result.indexed_count == 0
                            assert result.chunk_count == 0
                            assert any("Store error" in e for e in result.errors)

    def test_clear_index(self):
        """Test clearing the index."""
        with patch("mermaid_llm.rag.indexer.get_default_embeddings"):
            with patch("mermaid_llm.rag.indexer.rag_settings") as mock_settings:
                mock_settings.chroma_path = Path("/tmp/chroma")

                with patch("mermaid_llm.rag.indexer.Chroma") as mock_chroma:
                    mock_store = MagicMock()
                    mock_chroma.return_value = mock_store

                    indexer = DocumentIndexer()
                    # Access vector_store to initialize it
                    _ = indexer.vector_store
                    assert indexer._vector_store is not None

                    indexer.clear_index()

                    mock_store.delete_collection.assert_called_once()

    def test_get_document_count(self):
        """Test getting document count."""
        with patch("mermaid_llm.rag.indexer.get_default_embeddings"):
            with patch("mermaid_llm.rag.indexer.rag_settings") as mock_settings:
                mock_settings.chroma_path = Path("/tmp/chroma")

                with patch("mermaid_llm.rag.indexer.Chroma") as mock_chroma:
                    mock_collection = MagicMock()
                    mock_collection.count.return_value = 42

                    mock_store = MagicMock()
                    mock_store._collection = mock_collection
                    mock_chroma.return_value = mock_store

                    indexer = DocumentIndexer()
                    count = indexer.get_document_count()

                    assert count == 42

    def test_get_document_count_error(self):
        """Test document count returns 0 on error."""
        with patch("mermaid_llm.rag.indexer.get_default_embeddings"):
            with patch("mermaid_llm.rag.indexer.rag_settings") as mock_settings:
                mock_settings.chroma_path = Path("/tmp/chroma")

                with patch("mermaid_llm.rag.indexer.Chroma") as mock_chroma:
                    mock_store = MagicMock()
                    mock_store._collection.count.side_effect = Exception("Error")
                    mock_chroma.return_value = mock_store

                    indexer = DocumentIndexer()
                    count = indexer.get_document_count()

                    assert count == 0


class TestGetIndexer:
    """Tests for get_indexer function."""

    def test_returns_indexer_instance(self):
        """Test get_indexer returns DocumentIndexer."""
        with patch("mermaid_llm.rag.indexer.get_default_embeddings"):
            with patch("mermaid_llm.rag.indexer.rag_settings") as mock_settings:
                mock_settings.chroma_path = Path("/tmp/chroma")

                # Reset global indexer
                import mermaid_llm.rag.indexer as indexer_module

                indexer_module._default_indexer = None

                indexer = get_indexer()

                assert isinstance(indexer, DocumentIndexer)

    def test_returns_same_instance(self):
        """Test get_indexer returns singleton."""
        with patch("mermaid_llm.rag.indexer.get_default_embeddings"):
            with patch("mermaid_llm.rag.indexer.rag_settings") as mock_settings:
                mock_settings.chroma_path = Path("/tmp/chroma")

                # Reset global indexer
                import mermaid_llm.rag.indexer as indexer_module

                indexer_module._default_indexer = None

                indexer1 = get_indexer()
                indexer2 = get_indexer()

                assert indexer1 is indexer2
