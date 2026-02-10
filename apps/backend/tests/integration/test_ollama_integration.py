"""Ollama integration tests.

実際のOllamaサーバーとの結合テスト。
Ollamaが起動していない環境ではスキップされる。

実行方法:
  ollama serve  # 別ターミナルで起動
  ollama pull gemma3:1b  # テスト用モデルの取得
  pytest apps/backend/tests/integration/test_ollama_integration.py -v -m ollama
"""

import pytest
import httpx

from grc_ai.config import OllamaConfig
from grc_ai.providers.ollama_provider import OllamaProvider
from grc_ai.base import ChatMessage, MessageRole
from grc_ai.factory import create_ai_provider, AIProviderType
from grc_ai.config import AIConfig


OLLAMA_BASE_URL = "http://localhost:11434"
TEST_MODEL = "gemma3:1b"


def is_ollama_running() -> bool:
    """Ollamaサーバーが起動しているか確認。"""
    try:
        response = httpx.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5.0)
        return response.status_code == 200
    except (httpx.ConnectError, httpx.TimeoutException):
        return False


def is_model_available(model: str) -> bool:
    """指定モデルがダウンロード済みか確認。"""
    try:
        response = httpx.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5.0)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return any(m.get("name", "").startswith(model.split(":")[0]) for m in models)
    except (httpx.ConnectError, httpx.TimeoutException):
        pass
    return False


# Ollamaが起動していない場合は全テストをスキップ
pytestmark = [
    pytest.mark.ollama,
    pytest.mark.skipif(
        not is_ollama_running(),
        reason="Ollama server is not running at localhost:11434",
    ),
]


class TestOllamaConnection:
    """Ollama接続テスト。"""

    @pytest.mark.asyncio
    async def test_ollama_server_health(self):
        """Ollamaサーバーの稼働確認。"""
        response = httpx.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5.0)
        assert response.status_code == 200


@pytest.mark.skipif(
    not is_model_available(TEST_MODEL),
    reason=f"Model {TEST_MODEL} is not available (run: ollama pull {TEST_MODEL})",
)
class TestOllamaChat:
    """Ollamaチャットテスト。"""

    @pytest.fixture
    def provider(self):
        config = OllamaConfig(model_name=TEST_MODEL)
        return OllamaProvider(config)

    @pytest.mark.asyncio
    async def test_simple_chat(self, provider):
        """シンプルなチャット応答。"""
        messages = [
            ChatMessage(role=MessageRole.USER, content="Say hello in one word."),
        ]
        response = await provider.chat(messages, max_tokens=50)

        assert response.content != ""
        assert response.model is not None
        assert response.finish_reason == "stop"

    @pytest.mark.asyncio
    async def test_japanese_chat(self, provider):
        """日本語チャット応答。"""
        messages = [
            ChatMessage(
                role=MessageRole.SYSTEM,
                content="あなたはGRCコンサルタントです。日本語で回答してください。",
            ),
            ChatMessage(
                role=MessageRole.USER,
                content="内部統制とは何ですか？一文で答えてください。",
            ),
        ]
        response = await provider.chat(messages, max_tokens=200)
        assert response.content != ""
        assert len(response.content) > 5

    @pytest.mark.asyncio
    async def test_streaming_chat(self, provider):
        """ストリーミングチャット。"""
        messages = [
            ChatMessage(role=MessageRole.USER, content="Count from 1 to 3."),
        ]

        chunks = []
        async for chunk in provider.stream_chat(messages, max_tokens=100):
            chunks.append(chunk)

        assert len(chunks) > 0
        # 最後のチャンクにis_finalフラグ
        assert chunks[-1].is_final is True
        # 全チャンクを結合して内容確認
        full_text = "".join(c.content for c in chunks)
        assert len(full_text) > 0

    @pytest.mark.asyncio
    async def test_interview_dialogue(self, provider):
        """インタビュー対話シミュレーション。"""
        messages = [
            ChatMessage(
                role=MessageRole.SYSTEM,
                content="あなたはAIインタビュアーです。内部統制に関するヒアリングを実施してください。",
            ),
            ChatMessage(
                role=MessageRole.USER,
                content="月次決算プロセスについて質問してください。",
            ),
        ]

        response = await provider.chat(messages, temperature=0.3, max_tokens=300)
        assert response.content != ""
        assert response.usage.get("total_tokens", 0) > 0


@pytest.mark.skipif(
    not is_model_available(TEST_MODEL),
    reason=f"Model {TEST_MODEL} is not available",
)
class TestOllamaFactory:
    """ファクトリー経由でのOllamaプロバイダー生成テスト。"""

    @pytest.mark.asyncio
    async def test_create_local_provider(self):
        """create_ai_providerでローカルプロバイダーを生成。"""
        config = AIConfig(
            provider="local",
            ollama=OllamaConfig(model_name=TEST_MODEL),
        )
        provider = create_ai_provider(config)
        assert isinstance(provider, OllamaProvider)

        messages = [
            ChatMessage(role=MessageRole.USER, content="Reply with: OK"),
        ]
        response = await provider.chat(messages, max_tokens=10)
        assert response.content != ""
        await provider.close()

    @pytest.mark.asyncio
    async def test_create_local_provider_default_config(self):
        """デフォルト設定でのローカルプロバイダー生成。"""
        config = AIConfig(provider="local")
        provider = create_ai_provider(config)
        assert isinstance(provider, OllamaProvider)
        assert provider.config.model_name == "gemma3:1b"
