"""ヘルスチェックルートのユニットテスト。

テスト対象: apps/backend/src/grc_backend/api/routes/health.py
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from grc_backend.api.routes.health import HealthResponse, health_check, root

# --- HealthResponse モデルテスト ---


class TestHealthResponse:
    """HealthResponse Pydanticモデルのテスト。"""

    def test_valid_response(self):
        """正しい値で構築できること。"""
        resp = HealthResponse(
            status="healthy",
            database="healthy",
            redis="healthy",
            ai_provider="azure:configured",
            version="0.1.0",
            environment="development",
        )
        assert resp.status == "healthy"
        assert resp.database == "healthy"
        assert resp.redis == "healthy"
        assert resp.ai_provider == "azure:configured"
        assert resp.version == "0.1.0"
        assert resp.environment == "development"


# --- health_check テスト ---


class TestHealthCheck:
    """health_check エンドポイントのテスト。"""

    @pytest.mark.asyncio
    async def test_healthy_when_db_and_redis_up(self):
        """DB・Redis正常時にhealthyを返すこと。"""
        mock_db = AsyncMock()
        mock_db.execute.return_value = None

        mock_redis = AsyncMock()
        mock_redis.ping.return_value = True

        with (
            patch("grc_backend.api.routes.health.aioredis") as mock_aioredis,
            patch("grc_backend.api.routes.health.get_settings") as mock_settings,
        ):
            mock_aioredis.from_url.return_value = mock_redis
            settings = MagicMock()
            settings.redis_url = "redis://localhost:6379/0"
            settings.ai_provider = "azure"
            settings.azure_openai_api_key = "test-key"
            settings.environment = "development"
            mock_settings.return_value = settings

            result = await health_check(db=mock_db)
            assert result.status == "healthy"
            assert result.database == "healthy"
            assert result.redis == "healthy"
            assert result.ai_provider == "azure:configured"
            assert result.version == "0.1.0"
            assert result.environment == "development"

    @pytest.mark.asyncio
    async def test_degraded_when_db_down(self):
        """DB異常時にdegradedを返すこと。"""
        mock_db = AsyncMock()
        mock_db.execute.side_effect = Exception("DB接続エラー")

        mock_redis = AsyncMock()
        mock_redis.ping.return_value = True

        with (
            patch("grc_backend.api.routes.health.aioredis") as mock_aioredis,
            patch("grc_backend.api.routes.health.get_settings") as mock_settings,
        ):
            mock_aioredis.from_url.return_value = mock_redis
            settings = MagicMock()
            settings.redis_url = "redis://localhost:6379/0"
            settings.ai_provider = "local"
            settings.environment = "development"
            mock_settings.return_value = settings

            result = await health_check(db=mock_db)
            assert result.status == "degraded"
            assert result.database == "unhealthy"

    @pytest.mark.asyncio
    async def test_degraded_when_redis_down(self):
        """Redis異常時にdegradedを返すこと。"""
        mock_db = AsyncMock()
        mock_db.execute.return_value = None

        with (
            patch("grc_backend.api.routes.health.aioredis") as mock_aioredis,
            patch("grc_backend.api.routes.health.get_settings") as mock_settings,
        ):
            mock_aioredis.from_url.side_effect = Exception("Redis接続エラー")
            settings = MagicMock()
            settings.redis_url = "redis://localhost:6379/0"
            settings.ai_provider = "azure"
            settings.azure_openai_api_key = ""
            settings.environment = "development"
            mock_settings.return_value = settings

            result = await health_check(db=mock_db)
            assert result.status == "degraded"
            assert result.redis == "unhealthy"
            assert result.ai_provider == "azure:not_configured"


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
