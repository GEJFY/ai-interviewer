"""Model selection and provider management endpoints."""

import logging

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from grc_ai.models import (
    ALL_MODELS,
    PROVIDER_CAPABILITIES,
    RECOMMENDED_MODELS,
    ModelCapability,
    ModelTier,
    get_realtime_models,
)
from grc_backend.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()


class ModelResponse(BaseModel):
    """Single model response."""

    model_id: str
    display_name: str
    provider: str
    tier: str
    capabilities: list[str]
    context_window: int
    max_output_tokens: int
    input_cost_per_1k: float
    output_cost_per_1k: float
    latency_class: str
    supports_streaming: bool
    supports_tools: bool
    description: str


class ModelsListResponse(BaseModel):
    """Model list response."""

    models: list[ModelResponse]
    total: int


class RecommendedModelsResponse(BaseModel):
    """Recommended models by use case."""

    recommendations: dict[str, str]


class ProviderInfo(BaseModel):
    """Provider information."""

    provider: str
    is_configured: bool
    capabilities: dict


class ProvidersResponse(BaseModel):
    """Providers list response."""

    providers: list[ProviderInfo]
    active_provider: str


class ConnectionTestRequest(BaseModel):
    """Connection test request."""

    provider: str


class ConnectionTestResponse(BaseModel):
    """Connection test result."""

    provider: str
    status: str
    message: str
    model_used: str | None = None


@router.get("", response_model=ModelsListResponse)
async def list_models(
    provider: str | None = Query(None, description="Filter by provider"),
    tier: str | None = Query(None, description="Filter by tier"),
    capability: str | None = Query(None, description="Filter by capability"),
    realtime_only: bool = Query(False, description="Only real-time suitable models"),
) -> ModelsListResponse:
    """全モデル一覧を取得（フィルタ可能）。"""
    # 全モデルから開始し、各条件で順次フィルタ
    models = list(ALL_MODELS.values())

    if realtime_only:
        models = get_realtime_models(provider)
    else:
        if provider:
            models = [m for m in models if m.provider == provider]
        if tier:
            try:
                tier_enum = ModelTier(tier)
            except ValueError as err:
                raise HTTPException(
                    status_code=422,
                    detail=f"Invalid tier: '{tier}'. Valid values: {[t.value for t in ModelTier]}",
                ) from err
            models = [m for m in models if m.tier == tier_enum]
        if capability:
            try:
                cap_enum = ModelCapability(capability)
            except ValueError as err:
                raise HTTPException(
                    status_code=422,
                    detail=f"Invalid capability: '{capability}'. Valid values: {[c.value for c in ModelCapability]}",
                ) from err
            models = [m for m in models if cap_enum in m.capabilities]

    model_responses = [
        ModelResponse(
            model_id=m.model_id,
            display_name=m.display_name,
            provider=m.provider,
            tier=m.tier.value,
            capabilities=[c.value for c in m.capabilities],
            context_window=m.context_window,
            max_output_tokens=m.max_output_tokens,
            input_cost_per_1k=m.input_cost_per_1k,
            output_cost_per_1k=m.output_cost_per_1k,
            latency_class=m.latency_class.value,
            supports_streaming=m.supports_streaming,
            supports_tools=m.supports_tools,
            description=m.description,
        )
        for m in models
    ]

    return ModelsListResponse(models=model_responses, total=len(model_responses))


@router.get("/recommended", response_model=RecommendedModelsResponse)
async def get_recommended_models() -> RecommendedModelsResponse:
    """用途別推奨モデルを取得。"""
    return RecommendedModelsResponse(recommendations=RECOMMENDED_MODELS)


@router.get("/providers", response_model=ProvidersResponse)
async def list_providers() -> ProvidersResponse:
    """設定済みプロバイダー一覧とステータスを取得。"""
    settings = get_settings()

    providers = []
    for provider_name, caps in PROVIDER_CAPABILITIES.items():
        is_configured = _check_provider_configured(provider_name, settings)
        providers.append(
            ProviderInfo(
                provider=provider_name,
                is_configured=is_configured,
                capabilities=caps,
            )
        )

    return ProvidersResponse(
        providers=providers,
        active_provider=settings.ai_provider,
    )


@router.post("/test-connection", response_model=ConnectionTestResponse)
async def test_connection(request: ConnectionTestRequest) -> ConnectionTestResponse:
    """プロバイダー接続テスト。"""
    try:
        import os

        from grc_ai.base import ChatMessage, MessageRole
        from grc_ai.factory import create_ai_provider_from_env

        # テスト対象プロバイダーを一時的に設定
        original = os.environ.get("AI_PROVIDER")
        os.environ["AI_PROVIDER"] = request.provider

        try:
            provider = create_ai_provider_from_env()
            response = await provider.chat(
                messages=[
                    ChatMessage(
                        role=MessageRole.USER,
                        content="Reply with exactly: OK",
                    )
                ],
                temperature=0.0,
                max_tokens=10,
            )
            await provider.close()

            return ConnectionTestResponse(
                provider=request.provider,
                status="success",
                message="接続成功",
                model_used=response.model,
            )
        finally:
            if original is not None:
                os.environ["AI_PROVIDER"] = original
            elif "AI_PROVIDER" in os.environ:
                del os.environ["AI_PROVIDER"]

    except Exception as e:
        logger.warning(f"Connection test failed for {request.provider}: {e}")
        return ConnectionTestResponse(
            provider=request.provider,
            status="error",
            message=f"接続失敗: {str(e)}",
        )


def _check_provider_configured(provider: str, settings) -> bool:
    """Check if a provider has required credentials configured."""
    if provider in ("openai", "azure_openai"):
        return bool(settings.azure_openai_api_key and settings.azure_openai_endpoint)
    elif provider == "anthropic":
        return False  # Direct Anthropic not in settings
    elif provider == "aws_bedrock":
        return bool(settings.aws_access_key_id and settings.aws_secret_access_key)
    elif provider == "gcp_vertex":
        return bool(settings.gcp_project_id)
    elif provider == "local":
        return True  # Ollama requires no credentials
    return False
