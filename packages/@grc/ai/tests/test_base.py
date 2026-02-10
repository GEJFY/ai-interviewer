"""AI基盤モジュールのユニットテスト。

テスト対象: packages/@grc/ai/src/grc_ai/base.py
"""

from grc_ai.base import (
    AIProvider,
    ChatChunk,
    ChatMessage,
    ChatResponse,
    EmbeddingResponse,
    MessageRole,
)

# --- MessageRole テスト ---


class TestMessageRole:
    """MessageRole enum のテスト。"""

    def test_system_role(self):
        assert MessageRole.SYSTEM == "system"

    def test_user_role(self):
        assert MessageRole.USER == "user"

    def test_assistant_role(self):
        assert MessageRole.ASSISTANT == "assistant"

    def test_is_str_enum(self):
        """全値がstr型であること。"""
        for role in MessageRole:
            assert isinstance(role.value, str)


# --- ChatMessage テスト ---


class TestChatMessage:
    """ChatMessage のテスト。"""

    def test_construction(self):
        """role+contentで構築できること。"""
        msg = ChatMessage(role=MessageRole.USER, content="こんにちは")
        assert msg.role == MessageRole.USER
        assert msg.content == "こんにちは"

    def test_optional_name(self):
        """nameがオプショナルでNoneがデフォルトであること。"""
        msg = ChatMessage(role=MessageRole.USER, content="test")
        assert msg.name is None

    def test_with_name(self):
        """nameを指定できること。"""
        msg = ChatMessage(role=MessageRole.USER, content="test", name="interviewer")
        assert msg.name == "interviewer"


# --- ChatResponse テスト ---


class TestChatResponse:
    """ChatResponse のテスト。"""

    def test_construction(self):
        """必須フィールドで構築できること。"""
        resp = ChatResponse(content="応答テスト", model="gpt-5-nano")
        assert resp.content == "応答テスト"
        assert resp.model == "gpt-5-nano"

    def test_default_usage(self):
        """usageのデフォルトが空dictであること。"""
        resp = ChatResponse(content="test", model="test-model")
        assert resp.usage == {}

    def test_default_finish_reason(self):
        """finish_reasonのデフォルトがNoneであること。"""
        resp = ChatResponse(content="test", model="test-model")
        assert resp.finish_reason is None

    def test_with_all_fields(self):
        """全フィールド指定で構築できること。"""
        resp = ChatResponse(
            content="test",
            model="test-model",
            finish_reason="stop",
            usage={"prompt_tokens": 10, "completion_tokens": 20},
        )
        assert resp.finish_reason == "stop"
        assert resp.usage["prompt_tokens"] == 10


# --- ChatChunk テスト ---


class TestChatChunk:
    """ChatChunk のテスト。"""

    def test_default_is_final(self):
        """is_finalのデフォルトがFalseであること。"""
        chunk = ChatChunk(content="chunk")
        assert chunk.is_final is False

    def test_final_chunk(self):
        """最終チャンクの設定ができること。"""
        chunk = ChatChunk(content="", finish_reason="stop", is_final=True)
        assert chunk.is_final is True
        assert chunk.finish_reason == "stop"


# --- EmbeddingResponse テスト ---


class TestEmbeddingResponse:
    """EmbeddingResponse のテスト。"""

    def test_construction(self):
        """構築できること。"""
        resp = EmbeddingResponse(
            embedding=[0.1, 0.2, 0.3],
            model="text-embedding-3-large",
        )
        assert len(resp.embedding) == 3
        assert resp.model == "text-embedding-3-large"

    def test_default_usage(self):
        """usageのデフォルトが空dictであること。"""
        resp = EmbeddingResponse(embedding=[0.1], model="test")
        assert resp.usage == {}


# --- AIProvider Protocol テスト ---


class TestAIProviderProtocol:
    """AIProvider Protocol のテスト。"""

    def test_is_runtime_checkable(self):
        """runtime_checkableであること。"""
        assert hasattr(AIProvider, "__protocol_attrs__") or hasattr(
            AIProvider, "__abstractmethods__"
        )
