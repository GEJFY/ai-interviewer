"""FastAPI application entry point."""

import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from grc_backend.api.routes import (
    auth,
    demo,
    health,
    interviews,
    knowledge,
    models,
    projects,
    reports,
    tasks,
    templates,
)
from grc_backend.api.websocket import interview_ws
from grc_backend.config import get_settings
from grc_core.database import init_database

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan manager."""
    settings = get_settings()

    # Initialize database
    db = init_database(settings.database_url, echo=settings.debug)

    # Create tables in development
    if settings.is_development:
        await db.create_tables()

        # Auto-seed demo data when SEED_DEMO is enabled
        if os.environ.get("SEED_DEMO", "").lower() in ("true", "1", "yes"):
            from grc_backend.demo.seeder import DemoSeeder

            seeder = DemoSeeder(db)
            if not await seeder.is_seeded():
                result = await seeder.seed()
                logger.info(f"Demo data auto-seeded: {result}")

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

    # Demo endpoints (non-production only)
    if not settings.is_production:
        app.include_router(demo.router, prefix="/api/v1/demo", tags=["Demo"])

    return app


# Create application instance
app = create_app()
