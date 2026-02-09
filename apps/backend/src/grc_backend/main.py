"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from grc_backend.config import get_settings
from grc_backend.api.routes import (
    auth,
    projects,
    tasks,
    interviews,
    templates,
    reports,
    knowledge,
    health,
    models,
)
from grc_backend.api.websocket import interview_ws
from grc_core.database import init_database, get_database


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan manager."""
    settings = get_settings()

    # Initialize database
    db = init_database(settings.database_url, echo=settings.debug)

    # Create tables in development
    if settings.is_development:
        await db.create_tables()

    yield

    # Cleanup
    await db.close()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="AI Interview Tool API",
        description="GRC Advisory AI Interview System API",
        version="0.1.0",
        docs_url="/api/docs" if settings.is_development else None,
        redoc_url="/api/redoc" if settings.is_development else None,
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health.router, tags=["Health"])
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
    app.include_router(projects.router, prefix="/api/v1/projects", tags=["Projects"])
    app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["Tasks"])
    app.include_router(interviews.router, prefix="/api/v1/interviews", tags=["Interviews"])
    app.include_router(templates.router, prefix="/api/v1/templates", tags=["Templates"])
    app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])
    app.include_router(knowledge.router, prefix="/api/v1/knowledge", tags=["Knowledge"])
    app.include_router(models.router, prefix="/api/v1/models", tags=["Models"])

    # WebSocket endpoint
    app.include_router(interview_ws.router, prefix="/api/v1/interviews", tags=["WebSocket"])

    return app


# Create application instance
app = create_app()
