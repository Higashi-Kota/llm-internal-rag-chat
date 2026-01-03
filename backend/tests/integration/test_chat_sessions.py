"""Integration tests for chat session persistence."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from mermaid_llm.rag.retriever import SourceInfo


class TestChatSessionAPI:
    """Tests for chat session management endpoints."""

    @pytest.mark.asyncio
    async def test_create_session(self, async_client: AsyncClient):
        """Test creating a new chat session."""
        response = await async_client.post(
            "/api/rag/sessions",
            json={"title": "Test Session"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Session"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_create_session_without_title(self, async_client: AsyncClient):
        """Test creating a session without a title."""
        response = await async_client.post(
            "/api/rag/sessions",
            json={},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] is None
        assert "id" in data

    @pytest.mark.asyncio
    async def test_list_sessions_empty(self, async_client: AsyncClient):
        """Test listing sessions when none exist."""
        response = await async_client.get("/api/rag/sessions")

        assert response.status_code == 200
        data = response.json()
        assert data["sessions"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_sessions_with_data(self, async_client: AsyncClient):
        """Test listing sessions with existing data."""
        # Create multiple sessions
        for i in range(3):
            await async_client.post(
                "/api/rag/sessions",
                json={"title": f"Session {i}"},
            )

        response = await async_client.get("/api/rag/sessions")

        assert response.status_code == 200
        data = response.json()
        assert len(data["sessions"]) == 3
        assert data["total"] == 3

    @pytest.mark.asyncio
    async def test_get_session(self, async_client: AsyncClient):
        """Test getting a specific session."""
        # Create a session
        create_response = await async_client.post(
            "/api/rag/sessions",
            json={"title": "Test Session"},
        )
        session_id = create_response.json()["id"]

        # Get the session
        response = await async_client.get(f"/api/rag/sessions/{session_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["session"]["id"] == session_id
        assert data["session"]["title"] == "Test Session"
        assert data["messages"] == []

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, async_client: AsyncClient):
        """Test getting a non-existent session."""
        response = await async_client.get(
            "/api/rag/sessions/00000000-0000-0000-0000-000000000000"
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_session_invalid_id(self, async_client: AsyncClient):
        """Test getting a session with invalid ID format."""
        response = await async_client.get("/api/rag/sessions/invalid-id")

        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_delete_session(self, async_client: AsyncClient):
        """Test deleting a session."""
        # Create a session
        create_response = await async_client.post(
            "/api/rag/sessions",
            json={"title": "To Delete"},
        )
        session_id = create_response.json()["id"]

        # Delete the session
        response = await async_client.delete(f"/api/rag/sessions/{session_id}")

        assert response.status_code == 200
        assert response.json()["status"] == "deleted"

        # Verify it's gone
        get_response = await async_client.get(f"/api/rag/sessions/{session_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_session_not_found(self, async_client: AsyncClient):
        """Test deleting a non-existent session."""
        response = await async_client.delete(
            "/api/rag/sessions/00000000-0000-0000-0000-000000000000"
        )

        assert response.status_code == 404


class TestChatPersistence:
    """Tests for chat message persistence."""

    @pytest.mark.asyncio
    async def test_chat_with_session_persists_messages(self, async_client: AsyncClient):
        """Test that chat with session_id persists messages."""
        # Create a session
        create_response = await async_client.post(
            "/api/rag/sessions",
            json={"title": "Persistence Test"},
        )
        session_id = create_response.json()["id"]

        # Mock RAG response
        mock_result = {
            "response": "This is the response.",
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

        with patch("mermaid_llm.rag.run_rag", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = mock_result

            # Send chat with session_id
            response = await async_client.post(
                "/api/rag/chat",
                json={
                    "messages": [{"role": "user", "content": "Test question"}],
                    "session_id": session_id,
                },
            )

            assert response.status_code == 200

        # Verify messages were persisted
        session_response = await async_client.get(f"/api/rag/sessions/{session_id}")
        data = session_response.json()

        assert len(data["messages"]) == 2
        assert data["messages"][0]["role"] == "user"
        assert data["messages"][0]["content"] == "Test question"
        assert data["messages"][1]["role"] == "assistant"
        assert data["messages"][1]["content"] == "This is the response."
        assert data["messages"][1]["sources"] is not None
        assert len(data["messages"][1]["sources"]) == 1

    @pytest.mark.asyncio
    async def test_chat_without_session_does_not_persist(
        self, async_client: AsyncClient
    ):
        """Test that chat without session_id does not persist."""
        mock_result = {
            "response": "Response without persistence.",
            "sources": [],
            "model": "test-model",
            "provider": "test-provider",
        }

        with patch("mermaid_llm.rag.run_rag", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = mock_result

            response = await async_client.post(
                "/api/rag/chat",
                json={"messages": [{"role": "user", "content": "Test question"}]},
            )

            assert response.status_code == 200
            assert response.json()["session_id"] is None

    @pytest.mark.asyncio
    async def test_chat_with_invalid_session_returns_error(
        self, async_client: AsyncClient
    ):
        """Test that chat with invalid session_id returns error."""
        response = await async_client.post(
            "/api/rag/chat",
            json={
                "messages": [{"role": "user", "content": "Test question"}],
                "session_id": "00000000-0000-0000-0000-000000000000",
            },
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_stream_chat_with_session_persists_messages(
        self, async_client: AsyncClient
    ):
        """Test that streaming chat with session_id persists messages."""
        # Create a session
        create_response = await async_client.post(
            "/api/rag/sessions",
            json={"title": "Stream Persistence Test"},
        )
        session_id = create_response.json()["id"]

        # Mock streaming RAG response
        async def mock_stream(*args, **kwargs):
            yield {
                "event": "sources",
                "sources": [
                    SourceInfo(
                        filename="stream.pdf",
                        page=2,
                        slide=None,
                        sheet=None,
                        score=0.85,
                    )
                ],
            }
            yield {"event": "chunk", "response": "Streaming"}
            yield {"event": "chunk", "response": "Streaming response"}
            yield {
                "event": "done",
                "response": "Streaming response",
                "sources": [
                    SourceInfo(
                        filename="stream.pdf",
                        page=2,
                        slide=None,
                        sheet=None,
                        score=0.85,
                    )
                ],
                "model": "stream-model",
                "provider": "stream-provider",
            }

        with patch(
            "mermaid_llm.api.routers.rag.stream_rag", return_value=mock_stream()
        ):
            response = await async_client.post(
                "/api/rag/chat/stream",
                json={
                    "messages": [{"role": "user", "content": "Stream question"}],
                    "session_id": session_id,
                },
            )

            assert response.status_code == 200

        # Verify messages were persisted
        session_response = await async_client.get(f"/api/rag/sessions/{session_id}")
        data = session_response.json()

        assert len(data["messages"]) == 2
        assert data["messages"][0]["role"] == "user"
        assert data["messages"][0]["content"] == "Stream question"
        assert data["messages"][1]["role"] == "assistant"
        assert data["messages"][1]["content"] == "Streaming response"
        assert data["messages"][1]["model"] == "stream-model"
        assert data["messages"][1]["provider"] == "stream-provider"

    @pytest.mark.asyncio
    async def test_delete_session_deletes_messages(self, async_client: AsyncClient):
        """Test that deleting a session also deletes its messages."""
        # Create a session and add messages
        create_response = await async_client.post(
            "/api/rag/sessions",
            json={"title": "Delete Test"},
        )
        session_id = create_response.json()["id"]

        mock_result = {
            "response": "Test response",
            "sources": [],
            "model": "test-model",
            "provider": "test-provider",
        }

        with patch("mermaid_llm.rag.run_rag", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = mock_result
            await async_client.post(
                "/api/rag/chat",
                json={
                    "messages": [{"role": "user", "content": "Test"}],
                    "session_id": session_id,
                },
            )

        # Delete the session
        delete_response = await async_client.delete(f"/api/rag/sessions/{session_id}")
        assert delete_response.status_code == 200

        # Verify session and messages are gone
        get_response = await async_client.get(f"/api/rag/sessions/{session_id}")
        assert get_response.status_code == 404
