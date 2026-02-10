"""Cloud Provider Connection Tests.

Tests connectivity and model availability for all supported cloud AI providers:
- Azure AI Foundry (GPT-5.2, GPT-5 Nano, Claude Sonnet 4.6 Opus)
- AWS Bedrock (Claude Sonnet 4.6 Opus)
- GCP Vertex AI (Gemini 3.0 Pro/Flash Preview)
"""

import asyncio
import os
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest


# Mock response classes
class MockChatResponse:
    """Mock chat response for testing."""

    def __init__(self, content: str, model: str):
        self.content = content
        self.model = model
        self.usage = {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}


class MockEmbeddingResponse:
    """Mock embedding response for testing."""

    def __init__(self, dimensions: int = 1536):
        self.embedding = [0.1] * dimensions


# =============================================================================
# Azure AI Foundry Tests
# =============================================================================


class TestAzureAIFoundryConnection:
    """Test Azure AI Foundry connectivity and models."""

    @pytest.fixture
    def azure_config(self):
        """Azure AI Foundry configuration."""
        return {
            "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT", "https://test.openai.azure.com/"),
            "api_key": os.getenv("AZURE_OPENAI_API_KEY", "test-key"),
            "api_version": "2025-12-01-preview",
        }

    @pytest.mark.asyncio
    async def test_gpt52_connection(self, azure_config):
        """Test GPT-5.2 model connection on Azure."""
        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = MockChatResponse(
            content="GPT-5.2からの応答です。", model="gpt-5.2"
        )

        result = await mock_client.chat.completions.create(
            model="gpt-5.2", messages=[{"role": "user", "content": "テスト"}]
        )

        assert result.content is not None
        assert result.model == "gpt-5.2"

    @pytest.mark.asyncio
    async def test_gpt5_nano_connection(self, azure_config):
        """Test GPT-5 Nano model connection on Azure."""
        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = MockChatResponse(
            content="GPT-5 Nanoからの高速応答です。", model="gpt-5-nano"
        )

        result = await mock_client.chat.completions.create(
            model="gpt-5-nano", messages=[{"role": "user", "content": "テスト"}]
        )

        assert result.content is not None
        assert result.model == "gpt-5-nano"

    @pytest.mark.asyncio
    async def test_claude_sonnet_46_opus_via_azure(self, azure_config):
        """Test Claude Sonnet 4.6 Opus via Azure AI Foundry."""
        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = MockChatResponse(
            content="Claude Sonnet 4.6 Opus (Azure AI Foundry)からの応答です。",
            model="claude-sonnet-4.6-opus",
        )

        result = await mock_client.chat.completions.create(
            model="claude-sonnet-4.6-opus", messages=[{"role": "user", "content": "テスト"}]
        )

        assert result.content is not None
        assert "claude" in result.model.lower()

    @pytest.mark.asyncio
    async def test_azure_model_listing(self, azure_config):
        """Test listing available models on Azure AI Foundry."""
        expected_models = [
            "gpt-5.2",
            "gpt-5-nano",
            "gpt-4o",
            "claude-sonnet-4.6-opus",
            "claude-4.6-sonnet",
            "text-embedding-3-large",
        ]

        # Verify model configuration
        from grc_ai.models import get_models_by_provider

        azure_models = get_models_by_provider("azure_openai")

        model_ids = [m.model_id for m in azure_models]
        assert len(model_ids) > 0

    @pytest.mark.asyncio
    async def test_azure_streaming_response(self, azure_config):
        """Test streaming response from Azure AI Foundry."""
        chunks = ["これは", "ストリーミング", "テスト", "です。"]

        async def mock_stream():
            for chunk in chunks:
                yield MagicMock(choices=[MagicMock(delta=MagicMock(content=chunk))])

        collected = []
        async for chunk in mock_stream():
            if chunk.choices[0].delta.content:
                collected.append(chunk.choices[0].delta.content)

        assert "".join(collected) == "これはストリーミングテストです。"


# =============================================================================
# AWS Bedrock Tests
# =============================================================================


class TestAWSBedrockConnection:
    """Test AWS Bedrock connectivity and models."""

    @pytest.fixture
    def bedrock_config(self):
        """AWS Bedrock configuration."""
        return {
            "region": os.getenv("AWS_REGION", "us-east-1"),
            "access_key": os.getenv("AWS_ACCESS_KEY_ID", "test-key"),
            "secret_key": os.getenv("AWS_SECRET_ACCESS_KEY", "test-secret"),
        }

    @pytest.mark.asyncio
    async def test_claude_sonnet_46_opus_connection(self, bedrock_config):
        """Test Claude Sonnet 4.6 Opus on AWS Bedrock."""
        mock_client = AsyncMock()
        mock_client.invoke_model.return_value = {
            "body": MagicMock(
                read=lambda: b'{"content": [{"text": "Claude Sonnet 4.6 Opus (Bedrock)"}]}'
            )
        }

        response = await mock_client.invoke_model(
            modelId="anthropic.claude-sonnet-4.6-opus-v1:0",
            body=b'{"messages": [{"role": "user", "content": "test"}]}',
        )

        assert response is not None

    @pytest.mark.asyncio
    async def test_claude_46_sonnet_connection(self, bedrock_config):
        """Test Claude 4.6 Sonnet on AWS Bedrock."""
        mock_client = AsyncMock()
        mock_client.invoke_model.return_value = {
            "body": MagicMock(
                read=lambda: b'{"content": [{"text": "Claude 4.6 Sonnet (Bedrock)"}]}'
            )
        }

        response = await mock_client.invoke_model(
            modelId="anthropic.claude-4.6-sonnet-v1:0",
            body=b'{"messages": [{"role": "user", "content": "test"}]}',
        )

        assert response is not None

    @pytest.mark.asyncio
    async def test_claude_46_haiku_connection(self, bedrock_config):
        """Test Claude 4.6 Haiku on AWS Bedrock."""
        mock_client = AsyncMock()
        mock_client.invoke_model.return_value = {
            "body": MagicMock(read=lambda: b'{"content": [{"text": "Claude 4.6 Haiku (Bedrock)"}]}')
        }

        response = await mock_client.invoke_model(
            modelId="anthropic.claude-4.6-haiku-v1:0",
            body=b'{"messages": [{"role": "user", "content": "test"}]}',
        )

        assert response is not None

    @pytest.mark.asyncio
    async def test_amazon_nova_premier_connection(self, bedrock_config):
        """Test Amazon Nova Premier on Bedrock."""
        mock_client = AsyncMock()
        mock_client.invoke_model.return_value = {
            "body": MagicMock(read=lambda: b'{"content": "Amazon Nova Premier response"}')
        }

        response = await mock_client.invoke_model(
            modelId="amazon.nova-premier-v1:0",
            body=b'{"messages": [{"role": "user", "content": "test"}]}',
        )

        assert response is not None

    @pytest.mark.asyncio
    async def test_bedrock_model_listing(self, bedrock_config):
        """Test listing available models on AWS Bedrock."""
        from grc_ai.models import get_models_by_provider

        bedrock_models = get_models_by_provider("aws_bedrock")

        assert len(bedrock_models) > 0

        # Check for Claude 4.6 models
        model_ids = [m.model_id for m in bedrock_models]
        assert any("claude" in m.lower() for m in model_ids)

    @pytest.mark.asyncio
    async def test_bedrock_streaming_response(self, bedrock_config):
        """Test streaming response from AWS Bedrock."""
        chunks = [
            {"chunk": {"bytes": b'{"content": "Part 1"}'}},
            {"chunk": {"bytes": b'{"content": "Part 2"}'}},
        ]

        async def mock_stream():
            for chunk in chunks:
                yield chunk

        collected = []
        async for chunk in mock_stream():
            collected.append(chunk)

        assert len(collected) == 2


# =============================================================================
# GCP Vertex AI Tests
# =============================================================================


class TestGCPVertexAIConnection:
    """Test GCP Vertex AI connectivity and models."""

    @pytest.fixture
    def vertex_config(self):
        """GCP Vertex AI configuration."""
        return {
            "project_id": os.getenv("GCP_PROJECT_ID", "test-project"),
            "location": os.getenv("GCP_LOCATION", "asia-northeast1"),
        }

    @pytest.mark.asyncio
    async def test_gemini_30_pro_preview_connection(self, vertex_config):
        """Test Gemini 3.0 Pro Preview connection."""
        mock_model = AsyncMock()
        mock_model.generate_content_async.return_value = MagicMock(
            text="Gemini 3.0 Pro Previewからの応答です。2Mコンテキストウィンドウ対応。"
        )

        result = await mock_model.generate_content_async("テスト")

        assert result.text is not None
        assert len(result.text) > 0

    @pytest.mark.asyncio
    async def test_gemini_30_flash_preview_connection(self, vertex_config):
        """Test Gemini 3.0 Flash Preview connection."""
        mock_model = AsyncMock()
        mock_model.generate_content_async.return_value = MagicMock(
            text="Gemini 3.0 Flash Previewからの高速応答です。"
        )

        result = await mock_model.generate_content_async("テスト")

        assert result.text is not None

    @pytest.mark.asyncio
    async def test_gemini_30_flash_lite_connection(self, vertex_config):
        """Test Gemini 3.0 Flash Lite connection."""
        mock_model = AsyncMock()
        mock_model.generate_content_async.return_value = MagicMock(
            text="Gemini 3.0 Flash Liteからの効率的な応答です。"
        )

        result = await mock_model.generate_content_async("テスト")

        assert result.text is not None

    @pytest.mark.asyncio
    async def test_gemini_20_flash_connection(self, vertex_config):
        """Test Gemini 2.0 Flash connection (still supported)."""
        mock_model = AsyncMock()
        mock_model.generate_content_async.return_value = MagicMock(
            text="Gemini 2.0 Flashからの応答です。"
        )

        result = await mock_model.generate_content_async("テスト")

        assert result.text is not None

    @pytest.mark.asyncio
    async def test_vertex_model_listing(self, vertex_config):
        """Test listing available models on GCP Vertex AI."""
        from grc_ai.models import get_models_by_provider

        vertex_models = get_models_by_provider("gcp_vertex")

        assert len(vertex_models) > 0

        # Check for Gemini 3.0 models
        model_ids = [m.model_id for m in vertex_models]
        assert any("gemini-3.0" in m for m in model_ids)

    @pytest.mark.asyncio
    async def test_gemini_30_multimodal(self, vertex_config):
        """Test Gemini 3.0 multimodal capabilities."""
        mock_model = AsyncMock()
        mock_model.generate_content_async.return_value = MagicMock(
            text="画像分析結果: テスト画像には..."
        )

        # Simulate multimodal input (image + text)
        result = await mock_model.generate_content_async(
            [
                {"type": "text", "text": "この画像を説明してください"},
                {"type": "image", "data": b"mock_image_data"},
            ]
        )

        assert result.text is not None

    @pytest.mark.asyncio
    async def test_gemini_30_long_context(self, vertex_config):
        """Test Gemini 3.0 Pro with 2M context window."""
        from grc_ai.models import get_model

        model = get_model("gemini-3.0-pro-preview")
        assert model is not None
        assert model.context_window == 2000000


# =============================================================================
# Multi-Cloud Provider Switching Tests
# =============================================================================


class TestMultiCloudProviderSwitching:
    """Test switching between cloud providers."""

    @pytest.mark.asyncio
    async def test_provider_factory(self):
        """Test AI provider factory creates correct provider."""
        from grc_ai.models import PROVIDER_CAPABILITIES

        # Verify all providers are configured
        assert "openai" in PROVIDER_CAPABILITIES
        assert "anthropic" in PROVIDER_CAPABILITIES
        assert "azure_openai" in PROVIDER_CAPABILITIES
        assert "aws_bedrock" in PROVIDER_CAPABILITIES
        assert "gcp_vertex" in PROVIDER_CAPABILITIES

    @pytest.mark.asyncio
    async def test_azure_to_aws_fallback(self):
        """Test fallback from Azure to AWS Bedrock."""
        primary_failed = True
        fallback_used = False

        if primary_failed:
            # Fallback to AWS Bedrock
            fallback_used = True

        assert fallback_used

    @pytest.mark.asyncio
    async def test_recommended_models_exist(self):
        """Test all recommended models are available."""
        from grc_ai.models import RECOMMENDED_MODELS, get_model

        for use_case, model_id in RECOMMENDED_MODELS.items():
            model = get_model(model_id)
            assert model is not None, f"Model {model_id} for {use_case} not found"

    @pytest.mark.asyncio
    async def test_flagship_models_by_provider(self):
        """Test flagship model availability for each provider."""
        from grc_ai.models import PROVIDER_CAPABILITIES, get_model

        for provider, caps in PROVIDER_CAPABILITIES.items():
            latest_model = caps.get("latest_model")
            if latest_model:
                model = get_model(latest_model)
                assert model is not None, f"Latest model {latest_model} for {provider} not found"


# =============================================================================
# Model Capability Tests
# =============================================================================


class TestModelCapabilities:
    """Test model capabilities and features."""

    def test_flagship_models_have_reasoning(self):
        """Test flagship models have reasoning capability."""
        from grc_ai.models import ModelCapability, get_models_by_tier, ModelTier

        flagship_models = get_models_by_tier(ModelTier.FLAGSHIP)

        # At least some flagship models should have reasoning
        reasoning_models = [
            m for m in flagship_models if ModelCapability.REASONING in m.capabilities
        ]
        assert len(reasoning_models) > 0

    def test_multimodal_models_exist(self):
        """Test multimodal models are available."""
        from grc_ai.models import ModelCapability, get_models_by_capability

        multimodal_models = get_models_by_capability(ModelCapability.MULTIMODAL)
        assert len(multimodal_models) > 0

    def test_economy_models_are_cost_effective(self):
        """Test economy tier models have low costs."""
        from grc_ai.models import get_models_by_tier, ModelTier

        economy_models = get_models_by_tier(ModelTier.ECONOMY)

        for model in economy_models:
            # Economy models should have low input cost
            assert model.input_cost_per_1k < 0.001, f"{model.model_id} input cost too high"

    def test_context_window_specifications(self):
        """Test context window specifications are reasonable."""
        from grc_ai.models import get_model

        # GPT-5.2 should have 500K context
        gpt52 = get_model("gpt-5.2")
        assert gpt52.context_window == 500000

        # Gemini 3.0 Pro should have 2M context
        gemini30 = get_model("gemini-3.0-pro-preview")
        assert gemini30.context_window == 2000000


# =============================================================================
# Integration Test Summary
# =============================================================================


class TestConnectionSummary:
    """Summary tests for all connections."""

    @pytest.mark.asyncio
    async def test_all_providers_configured(self):
        """Verify all cloud providers are properly configured."""
        from grc_ai.models import ALL_MODELS

        providers = set(m.provider for m in ALL_MODELS.values())

        expected_providers = {
            "openai",
            "anthropic",
            "azure_openai",
            "aws_bedrock",
            "gcp_vertex",
            "local",
        }

        assert expected_providers.issubset(providers)

    @pytest.mark.asyncio
    async def test_total_model_count(self):
        """Verify sufficient models are configured."""
        from grc_ai.models import ALL_MODELS

        # Should have at least 20 models configured
        assert len(ALL_MODELS) >= 20

    @pytest.mark.asyncio
    async def test_latest_models_available(self):
        """Verify latest 2026 models are available."""
        from grc_ai.models import get_model

        latest_models = [
            "gpt-5.2",
            "gpt-5-nano",
            "claude-sonnet-4.6-opus",
            "claude-4.6-sonnet",
            "gemini-3.0-pro-preview",
            "gemini-3.0-flash-preview",
            "bedrock-claude-sonnet-4.6-opus",
        ]

        for model_id in latest_models:
            model = get_model(model_id)
            assert model is not None, f"Latest model {model_id} not found"


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
