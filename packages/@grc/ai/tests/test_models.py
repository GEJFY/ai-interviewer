"""Model catalog unit tests."""

from grc_ai.models import (
    ALL_MODELS,
    LOCAL_MODELS,
    PROVIDER_CAPABILITIES,
    RECOMMENDED_MODELS,
    LatencyClass,
    ModelCapability,
    ModelTier,
    get_model,
    get_models_by_capability,
    get_models_by_provider,
    get_models_by_tier,
    get_realtime_models,
    get_recommended_realtime_model,
)


class TestModelCatalog:
    """モデルカタログ基本テスト。"""

    def test_all_models_not_empty(self):
        """ALL_MODELSが空でないこと。"""
        assert len(ALL_MODELS) > 0

    def test_all_models_have_required_fields(self):
        """全モデルに必須フィールドがあること。"""
        for model_id, model in ALL_MODELS.items():
            assert model.model_id, f"{model_id}: model_id is empty"
            assert model.display_name, f"{model_id}: display_name is empty"
            assert model.provider, f"{model_id}: provider is empty"
            assert isinstance(model.tier, ModelTier), f"{model_id}: invalid tier"
            assert len(model.capabilities) > 0, f"{model_id}: no capabilities"
            assert model.context_window > 0 or model.model_id.startswith("nomic"), (
                f"{model_id}: invalid context_window"
            )

    def test_all_models_valid_latency_class(self):
        """全モデルに有効なlatency_classがあること。"""
        for model_id, model in ALL_MODELS.items():
            assert isinstance(model.latency_class, LatencyClass), (
                f"{model_id}: invalid latency_class"
            )

    def test_local_models_zero_cost(self):
        """ローカルモデルのコストが0であること。"""
        for model_id, model in LOCAL_MODELS.items():
            assert model.input_cost_per_1k == 0.0, f"{model_id}: input cost should be 0"
            assert model.output_cost_per_1k == 0.0, f"{model_id}: output cost should be 0"
            assert model.provider == "local", f"{model_id}: provider should be local"


class TestModelLookup:
    """モデル検索テスト。"""

    def test_get_model_existing(self):
        """存在するモデルの取得。"""
        model = get_model("gpt-5.2")
        assert model is not None
        assert model.display_name == "GPT-5.2"

    def test_get_model_nonexistent(self):
        """存在しないモデルの取得。"""
        model = get_model("nonexistent-model")
        assert model is None

    def test_get_models_by_provider_local(self):
        """ローカルプロバイダーのモデル取得。"""
        models = get_models_by_provider("local")
        assert len(models) > 0
        assert all(m.provider == "local" for m in models)

    def test_get_models_by_provider_azure(self):
        """Azureプロバイダーのモデル取得。"""
        models = get_models_by_provider("azure_openai")
        assert len(models) > 0

    def test_get_models_by_tier_economy(self):
        """ECONOMYティアのモデル取得。"""
        models = get_models_by_tier(ModelTier.ECONOMY)
        assert len(models) > 0
        assert all(m.tier == ModelTier.ECONOMY for m in models)

    def test_get_models_by_capability_embedding(self):
        """EMBEDDINGケイパビリティのモデル取得。"""
        models = get_models_by_capability(ModelCapability.EMBEDDING)
        assert len(models) > 0
        assert all(ModelCapability.EMBEDDING in m.capabilities for m in models)


class TestRealtimeModels:
    """リアルタイムモデル選択テスト。"""

    def test_get_realtime_models(self):
        """リアルタイムモデルの取得。"""
        models = get_realtime_models()
        assert len(models) > 0
        for m in models:
            assert m.latency_class in {LatencyClass.ULTRA_FAST, LatencyClass.FAST}
            assert ModelCapability.REALTIME in m.capabilities

    def test_get_realtime_models_sorted(self):
        """リアルタイムモデルが遅延順にソートされていること。"""
        models = get_realtime_models()
        fast_seen = False
        for m in models:
            if m.latency_class == LatencyClass.FAST:
                fast_seen = True
            if m.latency_class == LatencyClass.ULTRA_FAST:
                assert not fast_seen, "ULTRA_FAST should come before FAST"

    def test_get_recommended_realtime_economy(self):
        """コスパ重視のリアルタイムモデル推奨。"""
        model = get_recommended_realtime_model(tier=ModelTier.ECONOMY)
        assert model is not None
        assert model.latency_class in {LatencyClass.ULTRA_FAST, LatencyClass.FAST}

    def test_get_recommended_realtime_premium(self):
        """品質重視のリアルタイムモデル推奨。"""
        model = get_recommended_realtime_model(tier=ModelTier.PREMIUM)
        assert model is not None


class TestRecommendedModels:
    """推奨モデル設定テスト。"""

    def test_recommended_models_keys(self):
        """推奨モデル設定に必要なキーがあること。"""
        required_keys = [
            "interview_dialogue",
            "report_generation",
            "embedding",
            "local_test",
            "local_quality",
        ]
        for key in required_keys:
            assert key in RECOMMENDED_MODELS, f"Missing recommended key: {key}"

    def test_recommended_models_exist_in_catalog(self):
        """推奨モデルがカタログに存在すること。"""
        for use_case, model_id in RECOMMENDED_MODELS.items():
            assert model_id in ALL_MODELS, (
                f"Recommended model '{model_id}' for '{use_case}' not in catalog"
            )


class TestProviderCapabilities:
    """プロバイダーケイパビリティテスト。"""

    def test_all_providers_present(self):
        """全プロバイダーが登録されていること。"""
        expected = ["openai", "anthropic", "azure_openai", "aws_bedrock", "gcp_vertex", "local"]
        for p in expected:
            assert p in PROVIDER_CAPABILITIES, f"Missing provider: {p}"

    def test_local_provider_capabilities(self):
        """ローカルプロバイダーのケイパビリティ。"""
        local = PROVIDER_CAPABILITIES["local"]
        assert local["requires_ollama"] is True
        assert local["supports_realtime"] is True
        assert local["latest_model"] == "phi4"
        assert local["economy_model"] == "gemma3-1b"
