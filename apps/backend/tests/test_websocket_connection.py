"""Unit tests for WebSocket ConnectionManager."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from grc_backend.api.websocket.interview_ws import ConnectionManager


class TestConnectionManager:
    """Tests for the WebSocket ConnectionManager class."""

    @pytest.fixture
    def manager(self):
        return ConnectionManager()

    @pytest.fixture
    def mock_ws(self):
        ws = AsyncMock()
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        return ws

    @pytest.mark.asyncio
    async def test_connect(self, manager, mock_ws):
        """Connection is accepted and stored."""
        await manager.connect("interview-1", mock_ws)
        mock_ws.accept.assert_awaited_once()
        assert "interview-1" in manager.active_connections

    @pytest.mark.asyncio
    async def test_disconnect(self, manager, mock_ws):
        """Disconnection removes connection and agent."""
        await manager.connect("interview-1", mock_ws)
        manager.agents["interview-1"] = MagicMock()

        manager.disconnect("interview-1")
        assert "interview-1" not in manager.active_connections
        assert "interview-1" not in manager.agents

    def test_disconnect_unknown(self, manager):
        """Disconnecting unknown session does not raise."""
        manager.disconnect("unknown-id")

    @pytest.mark.asyncio
    async def test_send_message(self, manager, mock_ws):
        """Message is sent to the correct connection."""
        await manager.connect("interview-1", mock_ws)
        msg = {"type": "ai_response", "content": "hello"}

        await manager.send_message("interview-1", msg)
        mock_ws.send_json.assert_awaited_once_with(msg)

    @pytest.mark.asyncio
    async def test_send_message_unknown(self, manager):
        """Sending to unknown connection does not raise."""
        await manager.send_message("unknown", {"type": "test"})

    def test_get_agent_none(self, manager):
        assert manager.get_agent("interview-1") is None

    def test_set_and_get_agent(self, manager):
        agent = MagicMock()
        manager.set_agent("interview-1", agent)
        assert manager.get_agent("interview-1") is agent

    @pytest.mark.asyncio
    async def test_multiple_connections(self, manager):
        """Multiple connections can coexist."""
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        await manager.connect("id-1", ws1)
        await manager.connect("id-2", ws2)

        assert len(manager.active_connections) == 2
        manager.disconnect("id-1")
        assert len(manager.active_connections) == 1
        assert "id-2" in manager.active_connections
