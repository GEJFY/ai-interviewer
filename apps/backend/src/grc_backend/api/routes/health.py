"""Health check endpoints."""

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from grc_backend.api.deps import get_db
from grc_backend.config import get_settings

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    database: str
    redis: str
    ai_provider: str
    version: str
    environment: str


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    """Check application health."""
    settings = get_settings()

    # Check database connection
    try:
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    # Check Redis connection
    try:
        r = aioredis.from_url(settings.redis_url, socket_connect_timeout=2)
        await r.ping()
        await r.aclose()
        redis_status = "healthy"
    except Exception:
        redis_status = "unhealthy"

    # Check AI provider configuration
    provider = settings.ai_provider
    if provider == "azure":
        ai_status = "configured" if settings.azure_openai_api_key else "not_configured"
    elif provider == "aws":
        ai_status = "configured"
    elif provider == "gcp":
        ai_status = "configured" if settings.gcp_project_id else "not_configured"
    elif provider == "local":
        ai_status = "configured"
    else:
        ai_status = "unknown"

    # Overall status
    all_healthy = db_status == "healthy" and redis_status == "healthy"
    overall = "healthy" if all_healthy else "degraded"

    return HealthResponse(
        status=overall,
        database=db_status,
        redis=redis_status,
        ai_provider=f"{provider}:{ai_status}",
        version="0.1.0",
        environment=settings.environment,
    )


@router.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {
        "name": "AI Interview Tool API",
        "version": "0.1.0",
        "docs": "/api/docs",
    }
