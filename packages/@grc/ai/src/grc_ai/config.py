"""AI provider configuration."""

from pydantic import BaseModel, Field


class AzureOpenAIConfig(BaseModel):
    """Azure OpenAI configuration."""

    api_key: str
    endpoint: str  # https://your-resource.openai.azure.com/
    deployment_name: str = "gpt-5-nano"
    embedding_deployment: str = "text-embedding-3-large"
    api_version: str = "2025-12-01-preview"


class AWSBedrockConfig(BaseModel):
    """AWS Bedrock configuration."""

    access_key_id: str | None = None
    secret_access_key: str | None = None
    region: str = "ap-northeast-1"
    model_id: str = "anthropic.claude-sonnet-4-5-20250929-v1:0"
    embedding_model_id: str = "amazon.titan-embed-text-v2:0"


class GCPVertexConfig(BaseModel):
    """GCP Vertex AI configuration."""

    project_id: str
    location: str = "asia-northeast1"
    model_name: str = "gemini-2.5-flash"
    embedding_model: str = "text-embedding-005"
    credentials_path: str | None = None


class OllamaConfig(BaseModel):
    """Ollama (Local LLM) configuration."""

    base_url: str = "http://localhost:11434"
    model_name: str = "gemma3:1b"
    embedding_model: str = "nomic-embed-text"


class AIConfig(BaseModel):
    """Combined AI configuration."""

    provider: str = Field(default="azure", pattern="^(azure|aws|gcp|local)$")
    azure: AzureOpenAIConfig | None = None
    aws: AWSBedrockConfig | None = None
    gcp: GCPVertexConfig | None = None
    ollama: OllamaConfig | None = None

    # Common settings
    default_temperature: float = 0.7
    default_max_tokens: int = 4096
    timeout_seconds: int = 60
    max_retries: int = 3
