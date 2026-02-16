"""AI provider factory."""

from enum import StrEnum

from grc_ai.base import AIProvider
from grc_ai.config import AIConfig
from grc_ai.providers.aws_bedrock import AWSBedrockProvider
from grc_ai.providers.azure_foundry import AzureFoundryProvider
from grc_ai.providers.gcp_vertex import GCPVertexProvider
from grc_ai.providers.ollama_provider import OllamaProvider


class AIProviderType(StrEnum):
    """Supported AI provider types."""

    AZURE = "azure"
    AWS = "aws"
    GCP = "gcp"
    LOCAL = "local"


def create_ai_provider(config: AIConfig) -> AIProvider:
    """Create an AI provider based on configuration.

    Args:
        config: AI configuration specifying provider and credentials

    Returns:
        Configured AI provider instance

    Raises:
        ValueError: If provider type is invalid or config is missing
    """
    provider_type = AIProviderType(config.provider)

    match provider_type:
        case AIProviderType.AZURE:
            if config.azure is None:
                raise ValueError("Azure AI Foundry configuration is required")
            return AzureFoundryProvider(config.azure)

        case AIProviderType.AWS:
            if config.aws is None:
                raise ValueError("AWS Bedrock configuration is required")
            return AWSBedrockProvider(config.aws)

        case AIProviderType.GCP:
            if config.gcp is None:
                raise ValueError("GCP Vertex AI configuration is required")
            return GCPVertexProvider(config.gcp)

        case AIProviderType.LOCAL:
            from grc_ai.config import OllamaConfig

            ollama_config = config.ollama or OllamaConfig()
            return OllamaProvider(ollama_config)

        case _:
            raise ValueError(f"Unknown provider type: {config.provider}")


def create_ai_provider_from_env() -> AIProvider:
    """Create an AI provider from environment variables.

    Environment variables:
        AI_PROVIDER: Provider type (azure, aws, gcp, local)
        AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, etc.
        AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, etc.
        GCP_PROJECT_ID, GCP_LOCATION, etc.
        OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_EMBEDDING_MODEL

    Returns:
        Configured AI provider instance
    """
    import os

    provider = os.getenv("AI_PROVIDER", "azure")

    config_dict = {"provider": provider}

    if provider == "azure":
        config_dict["azure"] = {
            "api_key": os.environ["AZURE_OPENAI_API_KEY"],
            "endpoint": os.environ["AZURE_OPENAI_ENDPOINT"],
            "deployment_name": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-5-nano"),
            "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2025-12-01-preview"),
        }
    elif provider == "aws":
        config_dict["aws"] = {
            "access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
            "secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
            "region": os.getenv("AWS_REGION", "ap-northeast-1"),
            "model_id": os.getenv(
                "AWS_BEDROCK_MODEL_ID", "anthropic.claude-sonnet-4-5-20250929-v1:0"
            ),
        }
    elif provider == "gcp":
        config_dict["gcp"] = {
            "project_id": os.environ["GCP_PROJECT_ID"],
            "location": os.getenv("GCP_LOCATION", "asia-northeast1"),
            "model_name": os.getenv("GCP_VERTEX_MODEL", "gemini-2.5-flash"),
        }
    elif provider == "local":
        config_dict["ollama"] = {
            "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            "model_name": os.getenv("OLLAMA_MODEL", "gemma3:1b"),
            "embedding_model": os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text"),
        }

    config = AIConfig(**config_dict)
    return create_ai_provider(config)
