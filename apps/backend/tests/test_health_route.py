"""ヘルスチェックルートのユニットテスト。

テスト対象: apps/backend/src/grc_backend/api/routes/health.py
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from grc_backend.api.routes.health import HealthResponse, health_check, root


# --- HealthResponse モデルテスト ---


class TestHealthResponse:
    """HealthResponse Pydanticモデルのテスト。"""

    def test_valid_response(self):
        """正しい値で構築できること。"""
        resp = HealthResponse(status="healthy", database="healthy", version="0.1.0")
        assert resp.status == "healthy"
        assert resp.database == "healthy"
        assert resp.version == "0.1.0"


# --- health_check テスト ---


class TestHealthCheck:
    """health_check エンドポイントのテスト。"""

    @pytest.mark.asyncio
    async def test_healthy_when_db_up(self):
        """DB正常時にhealthyを返すこと。"""
        mock_db = AsyncMock()
        mock_db.execute.return_value = None  # SELECT 1 成功

        result = await health_check(db=mock_db)
        assert result.status == "healthy"
        assert result.database == "healthy"
        assert result.version == "0.1.0"

    @pytest.mark.asyncio
    async def test_degraded_when_db_down(self):
        """DB異常時にdegradedを返すこと。"""
        mock_db = AsyncMock()
        mock_db.execute.side_effect = Exception("DB接続エラー")

        result = await health_check(db=mock_db)
        assert result.status == "degraded"
        assert result.database == "unhealthy"


# --- root テスト ---


class TestRoot:
    """root エンドポイントのテスト。"""

    @pytest.mark.asyncio
    async def test_returns_app_info(self):
        """アプリケーション情報を返すこと。"""
        result = await root()
        assert result["name"] == "AI Interview Tool API"
        assert "version" in result
        assert "docs" in result
