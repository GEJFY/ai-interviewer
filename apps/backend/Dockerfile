# =============================================================================
# AI Interview Tool - Backend Dockerfile
# Multi-stage build for optimized production image
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Build dependencies
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS builder

# Install build dependencies and uv in single layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

WORKDIR /app

# Copy dependency files (cached layer when deps don't change)
COPY pyproject.toml ./
COPY packages/@grc/core/pyproject.toml packages/@grc/core/
COPY packages/@grc/ai/pyproject.toml packages/@grc/ai/

# Create virtual environment and install production dependencies
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN uv pip install --no-cache-dir \
    fastapi[standard]==0.115.0 \
    uvicorn[standard]==0.32.0 \
    pydantic==2.10.0 \
    pydantic-settings==2.6.0 \
    sqlalchemy[asyncio]==2.0.36 \
    asyncpg==0.30.0 \
    redis==5.2.0 \
    httpx==0.27.2 \
    python-jose[cryptography]==3.3.0 \
    passlib[bcrypt]==1.7.4 \
    python-multipart==0.0.17 \
    aiofiles==24.1.0 \
    tenacity==9.0.0 \
    structlog==24.4.0 \
    opentelemetry-api==1.28.0 \
    opentelemetry-sdk==1.28.0 \
    opentelemetry-instrumentation-fastapi==0.49b0 \
    opentelemetry-exporter-otlp==1.28.0 \
    azure-monitor-opentelemetry-exporter>=1.0.0b31 \
    msal>=1.31.0 \
    openai>=1.50.0 \
    azure-identity==1.19.0 \
    azure-cognitiveservices-speech==1.42.0 \
    boto3==1.35.0 \
    google-cloud-aiplatform==1.72.0 \
    anthropic==0.40.0 \
    ollama>=0.4.0 \
    "bcrypt>=4.0.0,<4.1.0"

# -----------------------------------------------------------------------------
# Stage 2: Production image
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS production

# Security: Create non-root user and install runtime deps in single layer
RUN groupadd -r appgroup && useradd -r -g appgroup appuser \
    && apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app/src:/app/packages/@grc/core/src:/app/packages/@grc/ai/src" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Copy application code
COPY apps/backend/src ./src
COPY packages/@grc/core/src ./packages/@grc/core/src
COPY packages/@grc/ai/src ./packages/@grc/ai/src

# Set ownership to non-root user
RUN chown -R appuser:appgroup /app

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "grc_backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# -----------------------------------------------------------------------------
# Stage 3: Development image (optional)
# -----------------------------------------------------------------------------
FROM production AS development

USER root

RUN pip install --no-cache-dir \
    pytest==8.3.0 \
    pytest-asyncio==0.24.0 \
    pytest-cov==6.0.0 \
    httpx==0.27.2 \
    mypy==1.13.0 \
    ruff==0.8.0 \
    pre-commit==4.0.0

USER appuser

CMD ["uvicorn", "grc_backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
