"""Models API endpoint unit tests."""

import pytest
from unittest.mock import patch, MagicMock


class TestModelsListEndpoint:
    """GET /api/v1/models テスト。"""

    @pytest.mark.asyncio
    async def test_list_all_models(self):
        """全モデル一覧の取得。"""
        from grc_ai.models import ALL_MODELS

        assert len(ALL_MODELS) > 0
        # ローカルモデルが含まれること
        local_models = [m for m in ALL_MODELS.values() if m.provider == "local"]
        assert len(local_models) > 0

    @pytest.mark.asyncio
    async def test_filter_by_provider(self):
        """プロバイダーフィルタのテスト。"""
        from grc_ai.models import get_models_by_provider

        azure_models = get_models_by_provider("azure_openai")
        assert len(azure_models) > 0
        assert all(m.provider == "azure_openai" for m in azure_models)

        local_models = get_models_by_provider("local")
        assert len(local_models) > 0
        assert all(m.provider == "local" for m in local_models)

    @pytest.mark.asyncio
    async def test_filter_by_tier(self):
        """ティアフィルタのテスト。"""
        from grc_ai.models import get_models_by_tier, ModelTier

        economy_models = get_models_by_tier(ModelTier.ECONOMY)
        assert len(economy_models) > 0
        assert all(m.tier == ModelTier.ECONOMY for m in economy_models)

    @pytest.mark.asyncio
    async def test_filter_realtime(self):
        """リアルタイムフィルタのテスト。"""
        from grc_ai.models import get_realtime_models, LatencyClass, ModelCapability

        rt_models = get_realtime_models()
        assert len(rt_models) > 0
        for m in rt_models:
            assert m.latency_class in {LatencyClass.ULTRA_FAST, LatencyClass.FAST}
            assert ModelCapability.REALTIME in m.capabilities


class TestRecommendedModelsEndpoint:
    """GET /api/v1/models/recommended テスト。"""

    @pytest.mark.asyncio
    async def test_recommended_models(self):
        """推奨モデルの取得。"""
        from grc_ai.models import RECOMMENDED_MODELS

        assert "interview_dialogue" in RECOMMENDED_MODELS
        assert "report_generation" in RECOMMENDED_MODELS
        assert "embedding" in RECOMMENDED_MODELS
        assert "local_test" in RECOMMENDED_MODELS


class TestProvidersEndpoint:
    """GET /api/v1/models/providers テスト。"""

    @pytest.mark.asyncio
    async def test_providers_list(self):
        """プロバイダー一覧の取得。"""
        from grc_ai.models import PROVIDER_CAPABILITIES

        providers = list(PROVIDER_CAPABILITIES.keys())
        assert "azure_openai" in providers
        assert "aws_bedrock" in providers
        assert "gcp_vertex" in providers
        assert "local" in providers


class TestConnectionTestEndpoint:
    """POST /api/v1/models/test-connection テスト。"""

    @pytest.mark.asyncio
    async def test_local_provider_check(self):
        """ローカルプロバイダーの設定チェック。"""
        from grc_backend.api.routes.models import _check_provider_configured

        # ローカルプロバイダーは常にTrue
        mock_settings = MagicMock()
        assert _check_provider_configured("local", mock_settings) is True

    @pytest.mark.asyncio
    async def test_azure_provider_check_configured(self):
        """Azureプロバイダーの設定チェック（設定済み）。"""
        from grc_backend.api.routes.models import _check_provider_configured

        mock_settings = MagicMock()
        mock_settings.azure_openai_api_key = "test-key"
        mock_settings.azure_openai_endpoint = "https://test.openai.azure.com/"
        assert _check_provider_configured("azure_openai", mock_settings) is True

    @pytest.mark.asyncio
    async def test_azure_provider_check_not_configured(self):
        """Azureプロバイダーの設定チェック（未設定）。"""
        from grc_backend.api.routes.models import _check_provider_configured

        mock_settings = MagicMock()
        mock_settings.azure_openai_api_key = ""
        mock_settings.azure_openai_endpoint = ""
        assert _check_provider_configured("azure_openai", mock_settings) is False
