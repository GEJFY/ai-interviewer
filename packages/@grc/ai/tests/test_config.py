"""AI設定モジュールのユニットテスト。

テスト対象: packages/@grc/ai/src/grc_ai/config.py
"""

import pytest
from pydantic import ValidationError

from grc_ai.config import (
    AIConfig,
    AWSBedrockConfig,
    AzureOpenAIConfig,
    GCPVertexConfig,
    OllamaConfig,
)

# --- AzureOpenAIConfig テスト ---


class TestAzureOpenAIConfig:
    """AzureOpenAIConfig のテスト。"""

    def test_default_deployment_name(self):
        """デフォルトのdeployment_nameが正しいこと。"""
        config = AzureOpenAIConfig(api_key="key", endpoint="https://test.openai.azure.com/")
        assert config.deployment_name == "gpt-5-nano"

    def test_default_api_version(self):
        """デフォルトのapi_versionが正しいこと。"""
        config = AzureOpenAIConfig(api_key="key", endpoint="https://test.openai.azure.com/")
        assert config.api_version == "2025-12-01-preview"

    def test_required_fields(self):
        """api_keyとendpointが必須であること。"""
        with pytest.raises(ValidationError):
            AzureOpenAIConfig()


# --- AWSBedrockConfig テスト ---


class TestAWSBedrockConfig:
    """AWSBedrockConfig のテスト。"""

    def test_default_region(self):
        """デフォルトリージョンがap-northeast-1であること。"""
        config = AWSBedrockConfig()
        assert config.region == "ap-northeast-1"

    def test_default_model_id(self):
        """デフォルトモデルIDがClaude Sonnet 4.5であること。"""
        config = AWSBedrockConfig()
        assert "claude-sonnet-4-5" in config.model_id

    def test_optional_credentials(self):
        """アクセスキーがオプショナルであること。"""
        config = AWSBedrockConfig()
        assert config.access_key_id is None
        assert config.secret_access_key is None


# --- GCPVertexConfig テスト ---


class TestGCPVertexConfig:
    """GCPVertexConfig のテスト。"""

    def test_project_id_required(self):
        """project_idが必須であること。"""
        with pytest.raises(ValidationError):
            GCPVertexConfig()

    def test_default_location(self):
        """デフォルトロケーションがasia-northeast1であること。"""
        config = GCPVertexConfig(project_id="test-project")
        assert config.location == "asia-northeast1"

    def test_default_model_name(self):
        """デフォルトモデル名がgemini-2.5-flashであること。"""
        config = GCPVertexConfig(project_id="test-project")
        assert config.model_name == "gemini-2.5-flash"


# --- OllamaConfig テスト ---


class TestOllamaConfig:
    """OllamaConfig のテスト。"""

    def test_default_base_url(self):
        """デフォルトbase_urlが正しいこと。"""
        config = OllamaConfig()
        assert config.base_url == "http://localhost:11434"

    def test_default_model_name(self):
        """デフォルトモデル名がgemma3:1bであること。"""
        config = OllamaConfig()
        assert config.model_name == "gemma3:1b"

    def test_default_embedding_model(self):
        """デフォルトembeddingモデルが正しいこと。"""
        config = OllamaConfig()
        assert config.embedding_model == "nomic-embed-text"

    def test_custom_values(self):
        """カスタム値が設定できること。"""
        config = OllamaConfig(
            base_url="http://gpu-server:11434",
            model_name="phi4",
            embedding_model="mxbai-embed-large",
        )
        assert config.base_url == "http://gpu-server:11434"
        assert config.model_name == "phi4"


# --- AIConfig テスト ---


class TestAIConfig:
    """AIConfig のテスト。"""

    def test_default_provider(self):
        """デフォルトプロバイダーがazureであること。"""
        config = AIConfig()
        assert config.provider == "azure"

    def test_valid_providers(self):
        """有効なプロバイダー値が受理されること。"""
        for provider in ["azure", "aws", "gcp", "local"]:
            config = AIConfig(provider=provider)
            assert config.provider == provider

    def test_invalid_provider_rejected(self):
        """無効なプロバイダー値が拒否されること。"""
        with pytest.raises(ValidationError):
            AIConfig(provider="invalid")

    def test_optional_cloud_configs(self):
        """クラウド設定がオプショナルであること。"""
        config = AIConfig()
        assert config.azure is None
        assert config.aws is None
        assert config.gcp is None
        assert config.ollama is None

    def test_default_common_settings(self):
        """共通設定のデフォルト値が正しいこと。"""
        config = AIConfig()
        assert config.default_temperature == 0.7
        assert config.default_max_tokens == 4096
        assert config.timeout_seconds == 60
        assert config.max_retries == 3
