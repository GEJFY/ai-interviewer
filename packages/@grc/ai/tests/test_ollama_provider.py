"""OllamaProvider unit tests."""

from unittest.mock import AsyncMock, patch

import pytest
from grc_ai.base import ChatMessage, MessageRole
from grc_ai.config import OllamaConfig
from grc_ai.providers.ollama_provider import OllamaProvider


class TestOllamaProviderInit:
    """OllamaProvider初期化テスト。"""

    def test_default_config(self):
        """デフォルト設定での初期化。"""
        config = OllamaConfig()
        provider = OllamaProvider(config)
        assert provider.config.base_url == "http://localhost:11434"
        assert provider.config.model_name == "gemma3:1b"
        assert provider.config.embedding_model == "nomic-embed-text"

    def test_custom_config(self):
        """カスタム設定での初期化。"""
        config = OllamaConfig(
            base_url="http://custom:11434",
            model_name="phi4",
            embedding_model="mxbai-embed-large",
        )
        provider = OllamaProvider(config)
        assert provider.config.base_url == "http://custom:11434"
        assert provider.config.model_name == "phi4"


class TestOllamaProviderChat:
    """OllamaProvider chatテスト。"""

    @pytest.fixture
    def provider(self):
        config = OllamaConfig()
        return OllamaProvider(config)

    @pytest.fixture
    def sample_messages(self):
        return [
            ChatMessage(role=MessageRole.SYSTEM, content="あなたはAIインタビュアーです。"),
            ChatMessage(role=MessageRole.USER, content="月次決算の手順を教えてください。"),
        ]

    @pytest.mark.asyncio
    async def test_chat_response(self, provider, sample_messages):
        """チャット応答のパース。"""
        mock_response = {
            "message": {"role": "assistant", "content": "月次決算の手順は以下の通りです。"},
            "model": "gemma3:1b",
            "done": True,
            "eval_count": 50,
            "prompt_eval_count": 30,
        }

        with patch.object(
            provider.client, "chat", new_callable=AsyncMock, return_value=mock_response
        ):
            response = await provider.chat(sample_messages)

        assert response.content == "月次決算の手順は以下の通りです。"
        assert response.model == "gemma3:1b"
        assert response.finish_reason == "stop"
        assert response.usage["prompt_tokens"] == 30
        assert response.usage["completion_tokens"] == 50

    @pytest.mark.asyncio
    async def test_chat_with_custom_model(self, provider, sample_messages):
        """カスタムモデル指定でのチャット。"""
        mock_response = {
            "message": {"role": "assistant", "content": "回答"},
            "model": "phi4",
            "done": True,
            "eval_count": 10,
            "prompt_eval_count": 20,
        }

        with patch.object(
            provider.client, "chat", new_callable=AsyncMock, return_value=mock_response
        ) as mock_chat:
            await provider.chat(sample_messages, model="phi4")

        call_args = mock_chat.call_args
        assert call_args.kwargs["model"] == "phi4"


class TestOllamaProviderStreamChat:
    """OllamaProvider stream_chatテスト。"""

    @pytest.fixture
    def provider(self):
        config = OllamaConfig()
        return OllamaProvider(config)

    @pytest.mark.asyncio
    async def test_stream_chat(self, provider):
        """ストリーミング応答テスト。"""
        messages = [ChatMessage(role=MessageRole.USER, content="テスト")]

        async def mock_stream():
            chunks = [
                {"message": {"content": "月次"}, "done": False},
                {"message": {"content": "決算"}, "done": False},
                {"message": {"content": ""}, "done": True},
            ]
            for chunk in chunks:
                yield chunk

        with patch.object(
            provider.client, "chat", new_callable=AsyncMock, return_value=mock_stream()
        ):
            collected = []
            async for chunk in provider.stream_chat(messages):
                collected.append(chunk)

        assert len(collected) == 3
        assert collected[0].content == "月次"
        assert collected[1].content == "決算"
        assert collected[2].is_final is True


class TestOllamaProviderEmbed:
    """OllamaProvider embeddingテスト。"""

    @pytest.fixture
    def provider(self):
        config = OllamaConfig()
        return OllamaProvider(config)

    @pytest.mark.asyncio
    async def test_embed_single(self, provider):
        """単一テキストのエンベディング。"""
        mock_response = {
            "embeddings": [[0.1, 0.2, 0.3, 0.4]],
            "prompt_eval_count": 5,
        }

        with patch.object(
            provider.client, "embed", new_callable=AsyncMock, return_value=mock_response
        ):
            response = await provider.embed("テストテキスト")

        assert len(response.embedding) == 4
        assert response.model == "nomic-embed-text"

    @pytest.mark.asyncio
    async def test_embed_batch(self, provider):
        """バッチエンベディング。"""
        mock_response = {
            "embeddings": [[0.1, 0.2], [0.3, 0.4]],
            "prompt_eval_count": 10,
        }

        with patch.object(
            provider.client, "embed", new_callable=AsyncMock, return_value=mock_response
        ):
            responses = await provider.embed_batch(["テキスト1", "テキスト2"])

        assert len(responses) == 2
        assert len(responses[0].embedding) == 2
