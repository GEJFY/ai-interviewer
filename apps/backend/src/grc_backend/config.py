"""Application configuration."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Environment
    environment: str = Field(default="development")
    debug: bool = Field(default=False)

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://grc_user:grc_password@localhost:5432/ai_interviewer"
    )

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")

    # Security
    secret_key: str = Field(default="dev-secret-key-change-in-production")
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)
    refresh_token_expire_days: int = Field(default=7)

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"]
    )

    # AI Provider
    ai_provider: str = Field(default="azure")

    # Azure OpenAI
    azure_openai_api_key: str = Field(default="")
    azure_openai_endpoint: str = Field(default="")
    azure_openai_deployment_name: str = Field(default="gpt-4")
    azure_openai_api_version: str = Field(default="2024-02-01")

    # AWS Bedrock
    aws_access_key_id: str = Field(default="")
    aws_secret_access_key: str = Field(default="")
    aws_region: str = Field(default="ap-northeast-1")
    aws_bedrock_model_id: str = Field(
        default="anthropic.claude-3-sonnet-20240229-v1:0"
    )

    # GCP Vertex AI
    gcp_project_id: str = Field(default="")
    gcp_location: str = Field(default="asia-northeast1")
    google_application_credentials: str = Field(default="")

    # Speech Provider (azure, aws, gcp)
    speech_provider: str = Field(default="azure")

    # Azure Speech
    azure_speech_key: str = Field(default="")
    azure_speech_region: str = Field(default="japaneast")

    # AWS Transcribe/Polly (uses aws_region from above)
    aws_transcribe_s3_bucket: str = Field(default="")

    # GCP Speech (uses gcp_project_id from above)

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
