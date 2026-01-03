"""Integration tests for RAG API endpoints."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from mermaid_llm.rag.retriever import SourceInfo


class TestRAGIndexAPI:
    """Tests for RAG indexing API endpoints."""

    @pytest.mark.asyncio
    async def test_get_index_status(self, async_client: AsyncClient):
        """Test getting index status."""
        with patch("mermaid_llm.api.routers.rag.get_indexer") as mock_get_indexer:
            mock_indexer = MagicMock()
            mock_indexer.get_document_count.return_value = 42
            mock_get_indexer.return_value = mock_indexer

            response = await async_client.get("/api/rag/index/status")

            assert response.status_code == 200
            data = response.json()
            assert "document_count" in data
            assert "chroma_dir" in data
            assert "docs_dir" in data

    @pytest.mark.asyncio
    async def test_clear_index(self, async_client: AsyncClient):
        """Test clearing the index."""
        with patch("mermaid_llm.api.routers.rag.get_indexer") as mock_get_indexer:
            mock_indexer = MagicMock()
            mock_get_indexer.return_value = mock_indexer

            response = await async_client.delete("/api/rag/index")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "cleared"
            mock_indexer.clear_index.assert_called_once()

    @pytest.mark.asyncio
    async def test_index_documents_success(
        self, async_client: AsyncClient, tmp_path: Path
    ):
        """Test indexing documents successfully."""
        # Create test documents
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "test.txt").write_text("Test content", encoding="utf-8")

        with patch("mermaid_llm.api.routers.rag.get_indexer") as mock_get_indexer:
            from mermaid_llm.rag.indexer import IndexResult

            mock_indexer = MagicMock()
            mock_indexer.index_documents.return_value = IndexResult(
                indexed_count=1,
                chunk_count=2,
                errors=[],
            )
            mock_get_indexer.return_value = mock_indexer

            response = await async_client.post(
                "/api/rag/index",
                json={"path": str(docs_dir), "clear_existing": False},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["indexed_count"] == 1
            assert data["chunk_count"] == 2
            assert data["errors"] == []

    @pytest.mark.asyncio
    async def test_index_documents_not_found(self, async_client: AsyncClient):
        """Test indexing with non-existent directory."""
        response = await async_client.post(
            "/api/rag/index",
            json={"path": "/non/existent/path"},
        )

        assert response.status_code == 400
        assert "does not exist" in response.json()["detail"]


class TestRAGChatAPI:
    """Tests for RAG chat API endpoints."""

    @pytest.mark.asyncio
    async def test_rag_chat_success(self, async_client: AsyncClient):
        """Test RAG chat endpoint."""
        mock_result = {
            "response": "This is the response based on the documents.",
            "sources": [
                SourceInfo(
                    filename="test.pdf",
                    page=1,
                    slide=None,
                    sheet=None,
                    score=0.95,
                )
            ],
            "model": "test-model",
            "provider": "test-provider",
        }

        # run_rag is imported inside the function, so patch at the rag module level
        with patch("mermaid_llm.rag.run_rag", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = mock_result

            response = await async_client.post(
                "/api/rag/chat",
                json={
                    "messages": [
                        {"role": "user", "content": "What is in the documents?"}
                    ]
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["response"] == "This is the response based on the documents."
            assert len(data["sources"]) == 1
            assert data["sources"][0]["filename"] == "test.pdf"
            assert data["model"] == "test-model"

    @pytest.mark.asyncio
    async def test_rag_chat_with_history(self, async_client: AsyncClient):
        """Test RAG chat with conversation history."""
        mock_result = {
            "response": "Follow-up response.",
            "sources": [],
            "model": "test-model",
            "provider": "test-provider",
        }

        with patch("mermaid_llm.rag.run_rag", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = mock_result

            response = await async_client.post(
                "/api/rag/chat",
                json={
                    "messages": [
                        {"role": "user", "content": "First question"},
                        {"role": "assistant", "content": "First answer"},
                        {"role": "user", "content": "Follow-up question"},
                    ]
                },
            )

            assert response.status_code == 200
            # Verify chat history was passed correctly
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            query = call_args[0][0]
            history = call_args[0][1]

            assert query == "Follow-up question"
            assert len(history) == 2
            assert history[0]["role"] == "user"
            assert history[1]["role"] == "assistant"

    @pytest.mark.asyncio
    async def test_rag_chat_error(self, async_client: AsyncClient):
        """Test RAG chat error handling."""
        with patch("mermaid_llm.rag.run_rag", new_callable=AsyncMock) as mock_run:
            mock_run.side_effect = Exception("LLM error")

            response = await async_client.post(
                "/api/rag/chat",
                json={"messages": [{"role": "user", "content": "Test question"}]},
            )

            assert response.status_code == 500
            assert "LLM error" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_rag_chat_empty_messages(self, async_client: AsyncClient):
        """Test RAG chat with empty messages."""
        response = await async_client.post(
            "/api/rag/chat",
            json={"messages": []},
        )

        # Should return validation error
        assert response.status_code == 422


class TestRAGStreamAPI:
    """Tests for RAG streaming API endpoints."""

    @pytest.mark.asyncio
    async def test_rag_chat_stream(self, async_client: AsyncClient):
        """Test streaming RAG chat endpoint."""

        async def mock_stream(*args, **kwargs):
            yield {"event": "sources", "sources": []}
            yield {"event": "chunk", "response": "Hello"}
            yield {"event": "chunk", "response": "Hello world"}
            yield {
                "event": "done",
                "response": "Hello world",
                "sources": [],
                "model": "test-model",
                "provider": "test-provider",
            }

        with patch(
            "mermaid_llm.api.routers.rag.stream_rag", return_value=mock_stream()
        ):
            response = await async_client.post(
                "/api/rag/chat/stream",
                json={"messages": [{"role": "user", "content": "Test question"}]},
            )

            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")

            # Parse SSE events
            events: list[str] = []
            for line in response.text.split("\n"):
                if line.startswith("event:"):
                    event_type = line.replace("event:", "").strip()
                    events.append(event_type)

            # Should have meta, sources, chunk, and done events
            assert "meta" in events
            assert "done" in events

    @pytest.mark.asyncio
    async def test_rag_chat_stream_error(self, async_client: AsyncClient):
        """Test streaming RAG chat error handling."""

        async def mock_stream_error(*args, **kwargs):
            raise Exception("Stream error")
            yield  # Make it a generator  # noqa: B901

        with patch(
            "mermaid_llm.api.routers.rag.stream_rag", return_value=mock_stream_error()
        ):
            response = await async_client.post(
                "/api/rag/chat/stream",
                json={"messages": [{"role": "user", "content": "Test question"}]},
            )

            assert response.status_code == 200
            # Stream should still start
            assert "text/event-stream" in response.headers.get("content-type", "")


class TestHealthCheck:
    """Tests for health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self, async_client: AsyncClient):
        """Test health check endpoint."""
        response = await async_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
