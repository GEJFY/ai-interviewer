"""Health check endpoints."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from grc_backend.api.deps import get_db

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    database: str
    version: str


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    """Check application health."""
    # Check database connection
    try:
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    return HealthResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        database=db_status,
        version="0.1.0",
    )


@router.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {
        "name": "AI Interview Tool API",
        "version": "0.1.0",
        "docs": "/api/docs",
    }
