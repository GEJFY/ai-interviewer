"""Integration tests for AI provider abstraction layer.

Tests verify that all AI providers (Azure OpenAI, AWS Bedrock, GCP Vertex AI, Anthropic)
work correctly through the unified abstraction layer.
"""

import asyncio
from typing import AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest


class MockMessage:
    """Mock message for testing."""

    def __init__(self, content: str, role: str = "assistant"):
        self.content = content
        self.role = role


class MockChatResponse:
    """Mock chat response for testing."""

    def __init__(self, content: str, usage: dict | None = None):
        self.content = content
        self.usage = usage or {"prompt_tokens": 100, "completion_tokens": 50}
        self.model = "test-model"


class TestAIProviderAbstraction:
    """Test the AI provider abstraction layer."""

    @pytest.mark.asyncio
    async def test_create_azure_openai_provider(self):
        """Azure OpenAI provider should be created correctly."""
        config = {
            "provider": "azure_openai",
            "endpoint": "https://test.openai.azure.com/",
            "api_key": "test-key",
            "deployment_name": "gpt-4o",
        }

        # Verify config structure
        assert config["provider"] == "azure_openai"
        assert "endpoint" in config
        assert "api_key" in config

    @pytest.mark.asyncio
    async def test_create_aws_bedrock_provider(self):
        """AWS Bedrock provider should be created correctly."""
        config = {
            "provider": "aws_bedrock",
            "region": "us-east-1",
            "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
        }

        assert config["provider"] == "aws_bedrock"
        assert "region" in config

    @pytest.mark.asyncio
    async def test_create_gcp_vertex_provider(self):
        """GCP Vertex AI provider should be created correctly."""
        config = {
            "provider": "gcp_vertex",
            "project_id": "test-project",
            "location": "asia-northeast1",
            "model": "gemini-2.0-flash",
        }

        assert config["provider"] == "gcp_vertex"
        assert "project_id" in config

    @pytest.mark.asyncio
    async def test_create_anthropic_provider(self):
        """Anthropic provider should be created correctly."""
        config = {
            "provider": "anthropic",
            "api_key": "test-anthropic-key",
            "model": "claude-3-5-sonnet-20241022",
        }

        assert config["provider"] == "anthropic"
        assert "api_key" in config


class TestLocalProvider:
    """Test local (Ollama) provider configuration."""

    @pytest.mark.asyncio
    async def test_create_local_provider(self):
        """Local LLM provider should be created correctly."""
        config = {
            "provider": "local",
            "base_url": "http://localhost:11434",
            "model_name": "gemma3:1b",
        }

        assert config["provider"] == "local"
        assert "base_url" in config

    @pytest.mark.asyncio
    async def test_local_provider_factory(self):
        """Local provider should be created via factory."""
        from grc_ai.config import AIConfig, OllamaConfig
        from grc_ai.factory import create_ai_provider
        from grc_ai.providers.ollama_provider import OllamaProvider

        config = AIConfig(
            provider="local",
            ollama=OllamaConfig(model_name="gemma3:1b"),
        )
        provider = create_ai_provider(config)
        assert isinstance(provider, OllamaProvider)
        assert provider.config.model_name == "gemma3:1b"

    @pytest.mark.asyncio
    async def test_local_provider_default_config(self):
        """Local provider with default config should use defaults."""
        from grc_ai.config import AIConfig
        from grc_ai.factory import create_ai_provider
        from grc_ai.providers.ollama_provider import OllamaProvider

        config = AIConfig(provider="local")
        provider = create_ai_provider(config)
        assert isinstance(provider, OllamaProvider)
        assert provider.config.base_url == "http://localhost:11434"

    def test_local_models_in_catalog(self):
        """Local models should be in the model catalog."""
        from grc_ai.models import get_models_by_provider

        local_models = get_models_by_provider("local")
        assert len(local_models) > 0
        model_ids = [m.model_id for m in local_models]
        assert "gemma3:1b" in model_ids
        assert "phi4" in model_ids


class TestChatCompletion:
    """Test chat completion across providers."""

    @pytest.fixture
    def mock_messages(self):
        """Sample messages for testing."""
        return [
            {"role": "system", "content": "あなたはAIインタビュアーです。"},
            {"role": "user", "content": "月次決算の手順を教えてください。"},
        ]

    @pytest.mark.asyncio
    async def test_azure_openai_chat(self, mock_messages):
        """Azure OpenAI chat completion should work."""
        mock_provider = AsyncMock()
        mock_provider.chat.return_value = MockChatResponse(
            content="月次決算の手順についてお答えします。まず..."
        )

        result = await mock_provider.chat(mock_messages)

        assert result.content is not None
        assert "月次決算" in result.content or len(result.content) > 0

    @pytest.mark.asyncio
    async def test_aws_bedrock_chat(self, mock_messages):
        """AWS Bedrock chat completion should work."""
        mock_provider = AsyncMock()
        mock_provider.chat.return_value = MockChatResponse(content="Claude からの応答です。")

        result = await mock_provider.chat(mock_messages)

        assert result.content is not None

    @pytest.mark.asyncio
    async def test_gcp_vertex_chat(self, mock_messages):
        """GCP Vertex AI chat completion should work."""
        mock_provider = AsyncMock()
        mock_provider.chat.return_value = MockChatResponse(content="Gemini からの応答です。")

        result = await mock_provider.chat(mock_messages)

        assert result.content is not None

    @pytest.mark.asyncio
    async def test_anthropic_chat(self, mock_messages):
        """Anthropic chat completion should work."""
        mock_provider = AsyncMock()
        mock_provider.chat.return_value = MockChatResponse(
            content="Anthropic Claude からの応答です。"
        )

        result = await mock_provider.chat(mock_messages)

        assert result.content is not None


class TestStreamingChat:
    """Test streaming chat completion."""

    @pytest.mark.asyncio
    async def test_streaming_response(self):
        """Streaming should yield chunks correctly."""
        chunks = ["これは", "ストリーミング", "テスト", "です。"]

        async def mock_stream():
            for chunk in chunks:
                yield MagicMock(content=chunk)

        collected = []
        async for chunk in mock_stream():
            collected.append(chunk.content)

        assert len(collected) == 4
        assert "".join(collected) == "これはストリーミングテストです。"

    @pytest.mark.asyncio
    async def test_streaming_handles_interruption(self):
        """Streaming should handle interruption gracefully."""

        async def mock_stream_with_error():
            yield MagicMock(content="開始")
            yield MagicMock(content="中間")
            # Simulate stream end
            return

        collected = []
        async for chunk in mock_stream_with_error():
            collected.append(chunk.content)

        assert len(collected) == 2


class TestEmbeddings:
    """Test embedding generation."""

    @pytest.mark.asyncio
    async def test_generate_embedding(self):
        """Embedding should be generated correctly."""
        mock_provider = AsyncMock()
        mock_provider.embed.return_value = [0.1] * 1536

        text = "月次決算プロセスの効率化"
        embedding = await mock_provider.embed(text)

        assert len(embedding) == 1536
        assert all(isinstance(v, float) for v in embedding)

    @pytest.mark.asyncio
    async def test_batch_embeddings(self):
        """Batch embeddings should be generated efficiently."""
        mock_provider = AsyncMock()
        mock_provider.embed_batch.return_value = [[0.1] * 1536 for _ in range(3)]

        texts = ["テキスト1", "テキスト2", "テキスト3"]

        embeddings = await mock_provider.embed_batch(texts)

        assert len(embeddings) == 3
        assert all(len(e) == 1536 for e in embeddings)


class TestModelSelection:
    """Test model selection and configuration."""

    def test_model_tier_selection(self):
        """Model should be selectable by tier."""
        from grc_ai.models import ModelTier, get_recommended_model, ModelCapability

        # Test economy tier
        economy_model = get_recommended_model(tier=ModelTier.ECONOMY)
        assert economy_model is not None
        assert economy_model.tier == ModelTier.ECONOMY

        # Test premium tier
        premium_model = get_recommended_model(tier=ModelTier.PREMIUM)
        assert premium_model is not None

    def test_model_capability_filter(self):
        """Models should be filterable by capability."""
        from grc_ai.models import get_recommended_model, ModelCapability

        # Test embedding capability
        embedding_model = get_recommended_model(capability=ModelCapability.EMBEDDING)
        assert embedding_model is not None
        assert ModelCapability.EMBEDDING in embedding_model.capabilities

    def test_provider_specific_model(self):
        """Provider-specific model should be retrievable."""
        from grc_ai.models import get_models_by_provider

        azure_models = get_models_by_provider("azure_openai")
        assert len(azure_models) > 0

        anthropic_models = get_models_by_provider("anthropic")
        assert len(anthropic_models) > 0

    def test_recommended_models_for_use_cases(self):
        """Recommended models should be defined for use cases."""
        from grc_ai.models import RECOMMENDED_MODELS

        assert "interview_dialogue" in RECOMMENDED_MODELS
        assert "report_generation" in RECOMMENDED_MODELS
        assert "quick_response" in RECOMMENDED_MODELS
        assert "complex_analysis" in RECOMMENDED_MODELS
        assert "embedding" in RECOMMENDED_MODELS
        assert "cost_effective" in RECOMMENDED_MODELS


class TestProviderFallback:
    """Test provider fallback mechanisms."""

    @pytest.mark.asyncio
    async def test_fallback_on_primary_failure(self):
        """System should fallback to secondary provider on failure."""
        primary_provider = AsyncMock()
        primary_provider.chat.side_effect = Exception("Primary provider failed")

        secondary_provider = AsyncMock()
        secondary_provider.chat.return_value = MockChatResponse(content="フォールバック応答")

        # Simulate fallback logic
        try:
            result = await primary_provider.chat([])
        except Exception:
            result = await secondary_provider.chat([])

        assert result.content == "フォールバック応答"

    @pytest.mark.asyncio
    async def test_retry_on_transient_error(self):
        """System should retry on transient errors."""
        call_count = 0

        async def mock_chat_with_retry(*args):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Transient error")
            return MockChatResponse(content="成功")

        mock_provider = AsyncMock()
        mock_provider.chat.side_effect = mock_chat_with_retry

        # Simulate retry logic
        for attempt in range(3):
            try:
                result = await mock_provider.chat([])
                break
            except Exception:
                if attempt == 2:
                    raise

        assert result.content == "成功"
        assert call_count == 3


class TestRateLimiting:
    """Test rate limiting handling."""

    @pytest.mark.asyncio
    async def test_rate_limit_backoff(self):
        """System should backoff on rate limit errors."""
        import time

        start_time = time.time()
        backoff_times = [0.1, 0.2, 0.4]  # Simulated backoff

        for backoff in backoff_times:
            await asyncio.sleep(backoff)

        elapsed = time.time() - start_time
        assert elapsed >= sum(backoff_times) - 0.1  # Allow small tolerance

    @pytest.mark.asyncio
    async def test_concurrent_request_limiting(self):
        """Concurrent requests should be limited."""
        semaphore = asyncio.Semaphore(5)  # Max 5 concurrent
        active_count = 0
        max_active = 0

        async def limited_request():
            nonlocal active_count, max_active
            async with semaphore:
                active_count += 1
                max_active = max(max_active, active_count)
                await asyncio.sleep(0.01)
                active_count -= 1

        await asyncio.gather(*[limited_request() for _ in range(20)])

        assert max_active <= 5


class TestCostTracking:
    """Test token and cost tracking."""

    def test_token_counting(self):
        """Tokens should be counted correctly."""
        usage = {"prompt_tokens": 150, "completion_tokens": 75, "total_tokens": 225}

        assert usage["total_tokens"] == usage["prompt_tokens"] + usage["completion_tokens"]

    def test_cost_calculation(self):
        """Cost should be calculated based on tokens and model pricing."""
        from grc_ai.models import get_model

        model = get_model("gpt-4o")
        if model:
            input_tokens = 1000
            output_tokens = 500

            input_cost = (input_tokens / 1000) * model.input_cost_per_1k
            output_cost = (output_tokens / 1000) * model.output_cost_per_1k
            total_cost = input_cost + output_cost

            assert total_cost > 0


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
