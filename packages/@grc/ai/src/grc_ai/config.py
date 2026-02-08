"""AI provider configuration."""

from pydantic import BaseModel, Field


class AzureOpenAIConfig(BaseModel):
    """Azure OpenAI configuration."""

    api_key: str
    endpoint: str  # https://your-resource.openai.azure.com/
    deployment_name: str = "gpt-4"
    embedding_deployment: str = "text-embedding-ada-002"
    api_version: str = "2024-02-01"


class AWSBedrockConfig(BaseModel):
    """AWS Bedrock configuration."""

    access_key_id: str | None = None
    secret_access_key: str | None = None
    region: str = "ap-northeast-1"
    model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    embedding_model_id: str = "amazon.titan-embed-text-v1"


class GCPVertexConfig(BaseModel):
    """GCP Vertex AI configuration."""

    project_id: str
    location: str = "asia-northeast1"
    model_name: str = "gemini-1.5-pro"
    embedding_model: str = "text-embedding-004"
    credentials_path: str | None = None


class AIConfig(BaseModel):
    """Combined AI configuration."""

    provider: str = Field(default="azure", pattern="^(azure|aws|gcp)$")
    azure: AzureOpenAIConfig | None = None
    aws: AWSBedrockConfig | None = None
    gcp: GCPVertexConfig | None = None

    # Common settings
    default_temperature: float = 0.7
    default_max_tokens: int = 4096
    timeout_seconds: int = 60
    max_retries: int = 3
