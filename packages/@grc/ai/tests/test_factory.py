"""AIプロバイダーファクトリーのユニットテスト。

テスト対象: packages/@grc/ai/src/grc_ai/factory.py
"""

from unittest.mock import patch

import pytest

from grc_ai.config import AIConfig, AWSBedrockConfig, AzureFoundryConfig, GCPVertexConfig
from grc_ai.factory import AIProviderType, create_ai_provider

# --- AIProviderType テスト ---


class TestAIProviderType:
    """AIProviderType enum のテスト。"""

    def test_all_values_exist(self):
        """全プロバイダータイプが定義されていること。"""
        assert AIProviderType.AZURE == "azure"
        assert AIProviderType.AWS == "aws"
        assert AIProviderType.GCP == "gcp"
        assert AIProviderType.LOCAL == "local"

    def test_is_str_enum(self):
        """StrEnumであること。"""
        for pt in AIProviderType:
            assert isinstance(pt.value, str)


# --- create_ai_provider テスト ---


class TestCreateAIProvider:
    """create_ai_provider のテスト。"""

    def test_local_creates_ollama_provider(self):
        """LOCAL指定でOllamaProviderが作成されること。"""
        from grc_ai.providers.ollama_provider import OllamaProvider

        config = AIConfig(provider="local")
        provider = create_ai_provider(config)
        assert isinstance(provider, OllamaProvider)

    def test_local_with_default_config(self):
        """LOCAL指定でollama未設定でもデフォルト設定で作成されること。"""
        config = AIConfig(provider="local", ollama=None)
        provider = create_ai_provider(config)
        # エラーなく作成されること
        assert provider is not None

    def test_azure_without_config_raises(self):
        """Azure設定なしでValueErrorが発生すること。"""
        config = AIConfig(provider="azure", azure=None)
        with pytest.raises(ValueError, match="Azure AI Foundry configuration is required"):
            create_ai_provider(config)

    def test_aws_without_config_raises(self):
        """AWS設定なしでValueErrorが発生すること。"""
        config = AIConfig(provider="aws", aws=None)
        with pytest.raises(ValueError, match="AWS Bedrock configuration is required"):
            create_ai_provider(config)

    def test_gcp_without_config_raises(self):
        """GCP設定なしでValueErrorが発生すること。"""
        config = AIConfig(provider="gcp", gcp=None)
        with pytest.raises(ValueError, match="GCP Vertex AI configuration is required"):
            create_ai_provider(config)

    @patch("grc_ai.providers.azure_foundry.AzureFoundryProvider.__init__", return_value=None)
    def test_azure_with_config_creates_provider(self, mock_init):
        """Azure設定ありでプロバイダーが作成されること。"""
        config = AIConfig(
            provider="azure",
            azure=AzureFoundryConfig(
                api_key="test-key",
                endpoint="https://test.openai.azure.com/",
            ),
        )
        provider = create_ai_provider(config)
        assert provider is not None

    @patch("grc_ai.providers.aws_bedrock.AWSBedrockProvider.__init__", return_value=None)
    def test_aws_with_config_creates_provider(self, mock_init):
        """AWS設定ありでプロバイダーが作成されること。"""
        config = AIConfig(
            provider="aws",
            aws=AWSBedrockConfig(region="us-east-1"),
        )
        provider = create_ai_provider(config)
        assert provider is not None

    @patch("grc_ai.providers.gcp_vertex.GCPVertexProvider.__init__", return_value=None)
    def test_gcp_with_config_creates_provider(self, mock_init):
        """GCP設定ありでプロバイダーが作成されること。"""
        config = AIConfig(
            provider="gcp",
            gcp=GCPVertexConfig(project_id="test-project"),
        )
        provider = create_ai_provider(config)
        assert provider is not None
