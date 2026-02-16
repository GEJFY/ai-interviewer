"""Application configuration."""

import json
from functools import lru_cache

from pydantic import Field, field_validator, model_validator
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

    # Logging
    log_level: str = Field(default="INFO")
    json_logs: bool = Field(default=False)

    # CORS (str | list[str] で pydantic-settings v2 の JSON パースエラーを回避)
    cors_origins: str | list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"]
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except (json.JSONDecodeError, TypeError):
                pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # Database connection pool
    db_pool_size: int = Field(default=10)
    db_max_overflow: int = Field(default=20)

    # Rate limiting
    rate_limit_enabled: bool = Field(default=False)
    rate_limit_requests: int = Field(default=100)
    rate_limit_window: int = Field(default=60)

    # AI Provider (azure, aws, gcp, local)
    ai_provider: str = Field(default="azure")

    # Azure AI Foundry (env vars keep AZURE_OPENAI_ prefix for Azure Portal compat)
    azure_openai_api_key: str = Field(default="")
    azure_openai_endpoint: str = Field(default="")
    azure_openai_deployment_name: str = Field(default="gpt-5-nano")
    azure_openai_api_version: str = Field(default="2025-12-01-preview")

    # AWS Bedrock
    aws_access_key_id: str = Field(default="")
    aws_secret_access_key: str = Field(default="")
    aws_region: str = Field(default="ap-northeast-1")
    aws_bedrock_model_id: str = Field(default="anthropic.claude-sonnet-4-5-20250929-v1:0")

    # GCP Vertex AI
    gcp_project_id: str = Field(default="")
    gcp_location: str = Field(default="asia-northeast1")
    gcp_vertex_model: str = Field(default="gemini-2.5-flash")
    google_application_credentials: str = Field(default="")

    # Ollama (Local LLM)
    ollama_base_url: str = Field(default="http://localhost:11434")
    ollama_model: str = Field(default="gemma3:1b")
    ollama_embedding_model: str = Field(default="nomic-embed-text")

    # Speech Provider (azure, aws, gcp)
    speech_provider: str = Field(default="azure")

    # Azure Speech
    azure_speech_key: str = Field(default="")
    azure_speech_region: str = Field(default="japaneast")

    # AWS Transcribe/Polly (uses aws_region from above)
    aws_transcribe_s3_bucket: str = Field(default="")

    # GCP Speech (uses gcp_project_id from above)

    # OpenTelemetry / Monitoring (opt-in)
    otel_enabled: bool = Field(default=False)
    otel_service_name: str = Field(default="ai-interviewer")
    applicationinsights_connection_string: str = Field(default="")

    # Azure Entra ID SSO (opt-in)
    azure_ad_client_id: str = Field(default="")
    azure_ad_client_secret: str = Field(default="")
    azure_ad_tenant_id: str = Field(default="")

    @model_validator(mode="after")
    def _validate_production_secrets(self) -> "Settings":
        """production環境でデフォルトSECRET_KEYの使用をブロック。"""
        if (
            self.environment == "production"
            and self.secret_key == "dev-secret-key-change-in-production"
        ):
            raise ValueError("SECRET_KEY must be set in production environment")
        return self

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"

    @property
    def sso_enabled(self) -> bool:
        """Check if Azure AD SSO is configured."""
        return bool(self.azure_ad_client_id and self.azure_ad_tenant_id)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
