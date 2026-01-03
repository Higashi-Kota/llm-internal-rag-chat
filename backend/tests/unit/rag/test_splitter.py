"""Tests for text splitter."""

from unittest.mock import patch

from langchain_core.documents import Document

from mermaid_llm.rag.splitter import (
    JAPANESE_SEPARATORS,
    create_text_splitter,
    text_splitter,
)


class TestJapaneseSeparators:
    """Tests for Japanese separator configuration."""

    def test_separators_order(self):
        """Test separators are in correct order (larger units first)."""
        expected_order = [
            "\n\n",  # Paragraph
            "\n",  # Line
            "。",  # Japanese period
            "、",  # Japanese comma
            "！",  # Japanese exclamation
            "？",  # Japanese question
            ".",  # English period
            ",",  # English comma
            " ",  # Space
            "",  # Fallback
        ]
        assert expected_order == JAPANESE_SEPARATORS

    def test_separators_contains_japanese_punctuation(self):
        """Test Japanese punctuation marks are included."""
        assert "。" in JAPANESE_SEPARATORS
        assert "、" in JAPANESE_SEPARATORS
        assert "！" in JAPANESE_SEPARATORS
        assert "？" in JAPANESE_SEPARATORS


class TestCreateTextSplitter:
    """Tests for create_text_splitter function."""

    def test_default_settings(self):
        """Test splitter uses default settings from config."""
        with patch("mermaid_llm.rag.splitter.rag_settings") as mock_settings:
            mock_settings.chunk_size = 500
            mock_settings.chunk_overlap = 100

            splitter = create_text_splitter()

            assert splitter._chunk_size == 500
            assert splitter._chunk_overlap == 100

    def test_custom_chunk_size(self):
        """Test splitter with custom chunk size."""
        with patch("mermaid_llm.rag.splitter.rag_settings") as mock_settings:
            mock_settings.chunk_size = 1000
            mock_settings.chunk_overlap = 200

            splitter = create_text_splitter(chunk_size=800)

            assert splitter._chunk_size == 800

    def test_custom_chunk_overlap(self):
        """Test splitter with custom chunk overlap."""
        with patch("mermaid_llm.rag.splitter.rag_settings") as mock_settings:
            mock_settings.chunk_size = 1000
            mock_settings.chunk_overlap = 200

            splitter = create_text_splitter(chunk_overlap=150)

            assert splitter._chunk_overlap == 150

    def test_custom_both_params(self):
        """Test splitter with both custom parameters."""
        splitter = create_text_splitter(chunk_size=600, chunk_overlap=50)

        assert splitter._chunk_size == 600
        assert splitter._chunk_overlap == 50

    def test_uses_japanese_separators(self):
        """Test splitter uses Japanese separators."""
        splitter = create_text_splitter(chunk_size=100, chunk_overlap=10)

        assert splitter._separators == JAPANESE_SEPARATORS


class TestTextSplitterFunctionality:
    """Tests for actual text splitting behavior."""

    def test_split_on_paragraph(self):
        """Test splitting on double newline (paragraph)."""
        # Both chunk_size and chunk_overlap must be provided to avoid
        # using default chunk_overlap which might be larger than chunk_size
        with patch("mermaid_llm.rag.splitter.rag_settings") as mock_settings:
            mock_settings.chunk_size = 40
            mock_settings.chunk_overlap = 0

            splitter = create_text_splitter(chunk_size=40, chunk_overlap=0)

            # Text designed to split on paragraph boundary
            text = "First paragraph text here.\n\nSecond paragraph text."
            docs = splitter.split_text(text)

            # Should split into 2 chunks at the paragraph boundary
            assert len(docs) >= 2
            # First chunk should contain first paragraph
            assert "First paragraph" in docs[0]

    def test_split_on_japanese_period(self):
        """Test splitting on Japanese period."""
        with patch("mermaid_llm.rag.splitter.rag_settings") as mock_settings:
            mock_settings.chunk_size = 20
            mock_settings.chunk_overlap = 0

            splitter = create_text_splitter(chunk_size=20, chunk_overlap=0)

            # Text longer than chunk_size
            text = "これは最初の文章です。次の文章です。最後の文章です。"
            docs = splitter.split_text(text)

            # Should split on 。
            assert len(docs) >= 2

    def test_split_documents_preserves_metadata(self):
        """Test split_documents preserves document metadata."""
        with patch("mermaid_llm.rag.splitter.rag_settings") as mock_settings:
            mock_settings.chunk_size = 30
            mock_settings.chunk_overlap = 0

            splitter = create_text_splitter(chunk_size=30, chunk_overlap=0)

            # Content longer than chunk_size
            doc = Document(
                page_content="First part with longer text.\n\nSecond part with more content.",
                metadata={"source": "test.txt", "page": 1},
            )
            chunks = splitter.split_documents([doc])

            assert len(chunks) >= 2
            for chunk in chunks:
                assert chunk.metadata["source"] == "test.txt"
                assert chunk.metadata["page"] == 1

    def test_chunk_overlap(self):
        """Test chunk overlap creates overlapping content."""
        with patch("mermaid_llm.rag.splitter.rag_settings") as mock_settings:
            mock_settings.chunk_size = 20
            mock_settings.chunk_overlap = 5

            splitter = create_text_splitter(chunk_size=20, chunk_overlap=5)

            # Long text that will be split
            text = "A" * 10 + " " + "B" * 10 + " " + "C" * 10
            docs = splitter.split_text(text)

            # Should have multiple chunks with some overlap
            assert len(docs) >= 2

    def test_long_text_split(self):
        """Test splitting long Japanese text."""
        with patch("mermaid_llm.rag.splitter.rag_settings") as mock_settings:
            mock_settings.chunk_size = 100
            mock_settings.chunk_overlap = 20

            splitter = create_text_splitter(chunk_size=100, chunk_overlap=20)

            # Create a long Japanese text
            text = "これはテストです。" * 20
            docs = splitter.split_text(text)

            # Should be split into multiple chunks
            assert len(docs) > 1
            # Each chunk should be within size limit (with some tolerance)
            for doc in docs:
                assert len(doc) <= 120  # Allow some buffer


class TestDefaultSplitter:
    """Tests for the default splitter instance."""

    def test_default_splitter_exists(self):
        """Test default splitter is created."""
        assert text_splitter is not None

    def test_default_splitter_can_split(self):
        """Test default splitter can split text."""
        text = "Test content.\n\nMore content."
        docs = text_splitter.split_text(text)

        assert len(docs) >= 1
