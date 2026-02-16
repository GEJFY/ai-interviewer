"""WebSocket認証のユニットテスト。

テスト対象: apps/backend/src/grc_backend/api/websocket/interview_ws.py
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from jose import jwt


def _create_token(sub: str, token_type: str = "access", secret: str = "test-secret"):
    """テスト用JWTトークンを生成する。"""
    from datetime import UTC, datetime, timedelta

    payload = {
        "sub": sub,
        "type": token_type,
        "exp": datetime.now(UTC) + timedelta(minutes=30),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


class TestWebSocketAuthentication:
    """WebSocket接続時のJWT認証テスト。"""

    @pytest.fixture
    def mock_settings(self):
        settings = MagicMock()
        settings.secret_key = "test-secret"
        settings.jwt_algorithm = "HS256"
        return settings

    @pytest.fixture
    def mock_websocket(self):
        ws = AsyncMock()
        ws.query_params = {}
        ws.headers = {}
        return ws

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @patch("grc_backend.api.websocket.interview_ws.get_settings")
    @patch("grc_backend.api.websocket.interview_ws.UserRepository")
    async def test_authenticate_with_valid_token(
        self, mock_user_repo_cls, mock_get_settings, mock_websocket, mock_settings, mock_db
    ):
        """有効なトークンで認証が成功すること。"""
        from grc_backend.api.websocket.interview_ws import _authenticate_websocket

        mock_get_settings.return_value = mock_settings
        token = _create_token("user-123", secret="test-secret")
        mock_websocket.query_params = {"token": token}

        mock_user = MagicMock()
        mock_user.id = "user-123"
        mock_user_repo_cls.return_value.get = AsyncMock(return_value=mock_user)

        result = await _authenticate_websocket(mock_websocket, mock_db)
        assert result is not None
        assert result.id == "user-123"

    @patch("grc_backend.api.websocket.interview_ws.get_settings")
    async def test_reject_missing_token(
        self, mock_get_settings, mock_websocket, mock_settings, mock_db
    ):
        """トークンなしで接続が拒否されること。"""
        from grc_backend.api.websocket.interview_ws import _authenticate_websocket

        mock_get_settings.return_value = mock_settings
        mock_websocket.query_params = {}

        result = await _authenticate_websocket(mock_websocket, mock_db)
        assert result is None
        mock_websocket.close.assert_called_once_with(code=4001, reason="Authentication required")

    @patch("grc_backend.api.websocket.interview_ws.get_settings")
    async def test_reject_refresh_token(
        self, mock_get_settings, mock_websocket, mock_settings, mock_db
    ):
        """リフレッシュトークンで接続が拒否されること。"""
        from grc_backend.api.websocket.interview_ws import _authenticate_websocket

        mock_get_settings.return_value = mock_settings
        token = _create_token("user-123", token_type="refresh", secret="test-secret")
        mock_websocket.query_params = {"token": token}

        result = await _authenticate_websocket(mock_websocket, mock_db)
        assert result is None
        mock_websocket.close.assert_called_once_with(code=4001, reason="Invalid token type")

    @patch("grc_backend.api.websocket.interview_ws.get_settings")
    async def test_reject_invalid_token(
        self, mock_get_settings, mock_websocket, mock_settings, mock_db
    ):
        """不正なトークンで接続が拒否されること。"""
        from grc_backend.api.websocket.interview_ws import _authenticate_websocket

        mock_get_settings.return_value = mock_settings
        mock_websocket.query_params = {"token": "invalid.jwt.token"}

        result = await _authenticate_websocket(mock_websocket, mock_db)
        assert result is None
        mock_websocket.close.assert_called_once_with(code=4001, reason="Invalid or expired token")

    @patch("grc_backend.api.websocket.interview_ws.get_settings")
    @patch("grc_backend.api.websocket.interview_ws.UserRepository")
    async def test_reject_nonexistent_user(
        self, mock_user_repo_cls, mock_get_settings, mock_websocket, mock_settings, mock_db
    ):
        """存在しないユーザーのトークンが拒否されること。"""
        from grc_backend.api.websocket.interview_ws import _authenticate_websocket

        mock_get_settings.return_value = mock_settings
        token = _create_token("nonexistent-user", secret="test-secret")
        mock_websocket.query_params = {"token": token}
        mock_user_repo_cls.return_value.get = AsyncMock(return_value=None)

        result = await _authenticate_websocket(mock_websocket, mock_db)
        assert result is None
        mock_websocket.close.assert_called_once_with(code=4001, reason="User not found")
