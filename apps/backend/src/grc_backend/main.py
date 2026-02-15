"""FastAPI application entry point."""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

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
from grc_backend.core.errors import AppError, app_error_handler, generic_exception_handler
from grc_backend.core.logging import get_logger, setup_logging
from grc_backend.core.security import SecurityConfig, setup_security
from grc_core.database import init_database

logger = get_logger(__name__)


def _validate_ai_provider(settings) -> None:
    """Validate AI provider configuration on startup."""
    provider = settings.ai_provider
    if provider == "azure":
        if not settings.azure_openai_api_key or not settings.azure_openai_endpoint:
            logger.warning("Azure OpenAI credentials not configured")
    elif provider == "aws":
        if not settings.aws_access_key_id:
            logger.info("AWS credentials not set - using IAM role authentication")
    elif provider == "gcp":
        if not settings.gcp_project_id:
            logger.warning("GCP project ID not configured")
    elif provider == "local":
        logger.info(
            "Using local LLM (Ollama)",
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
        )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan manager."""
    settings = get_settings()

    # Setup structured logging
    setup_logging(
        service_name="ai-interviewer",
        environment=settings.environment,
        log_level=settings.log_level,
        json_output=settings.json_logs,
    )

    logger.info("Application starting", environment=settings.environment)

    # Validate AI provider configuration
    _validate_ai_provider(settings)

    # Initialize database
    db = init_database(settings.database_url, echo=settings.debug)

    # Create tables (idempotent - safe for all environments)
    await db.create_tables()

    # Auto-seed demo data when SEED_DEMO is enabled (development only)
    if settings.is_development:
        if os.environ.get("SEED_DEMO", "").lower() in ("true", "1", "yes"):
            from grc_backend.demo.seeder import DemoSeeder

            seeder = DemoSeeder(db)
            if not await seeder.is_seeded():
                result = await seeder.seed()
                logger.info("Demo data auto-seeded", result=result)

    logger.info(
        "Application started successfully",
        environment=settings.environment,
        ai_provider=settings.ai_provider,
    )

    yield

    # Cleanup
    logger.info("Application shutting down")
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

    # Store debug mode in app state for error handlers
    app.state.debug = settings.debug

    # Register error handlers
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # Security middleware (CORS + security headers + rate limiting)
    security_config = SecurityConfig(
        cors_origins=settings.cors_origins,
        rate_limit_enabled=settings.rate_limit_enabled,
        rate_limit_requests=settings.rate_limit_requests,
        rate_limit_window=settings.rate_limit_window,
        hsts_enabled=settings.is_production,
        csp_enabled=settings.is_production,
        debug=settings.debug,
    )
    setup_security(app, security_config)

    # Include routers
    app.include_router(health.router, prefix="/api/v1", tags=["Health"])
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
