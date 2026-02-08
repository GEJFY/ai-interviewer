# =============================================================================
# AI Interview Tool - Backend Dockerfile
# Multi-stage build for optimized production image
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Build dependencies
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install uv for faster package management
RUN pip install uv

# Copy dependency files
COPY pyproject.toml ./
COPY packages/@grc/core/pyproject.toml packages/@grc/core/
COPY packages/@grc/ai/pyproject.toml packages/@grc/ai/
COPY packages/@grc/infrastructure/pyproject.toml packages/@grc/infrastructure/

# Create virtual environment and install dependencies
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install production dependencies only
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
    azure-identity==1.19.0 \
    azure-cognitiveservices-speech==1.42.0 \
    boto3==1.35.0 \
    google-cloud-aiplatform==1.72.0 \
    anthropic==0.40.0

# -----------------------------------------------------------------------------
# Stage 2: Production image
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS production

# Security: Create non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/app/src:/app/packages/@grc/core/src:/app/packages/@grc/ai/src:/app/packages/@grc/infrastructure/src"

# Copy application code
COPY apps/backend/src ./src
COPY packages/@grc/core/src ./packages/@grc/core/src
COPY packages/@grc/ai/src ./packages/@grc/ai/src
COPY packages/@grc/infrastructure/src ./packages/@grc/infrastructure/src

# Set ownership to non-root user
RUN chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Expose port
EXPOSE 8000

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8000

# Default command
CMD ["uvicorn", "grc_backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# -----------------------------------------------------------------------------
# Stage 3: Development image (optional)
# -----------------------------------------------------------------------------
FROM production AS development

# Switch to root for development setup
USER root

# Install development tools
RUN pip install --no-cache-dir \
    pytest==8.3.0 \
    pytest-asyncio==0.24.0 \
    pytest-cov==6.0.0 \
    httpx==0.27.2 \
    mypy==1.13.0 \
    ruff==0.8.0 \
    pre-commit==4.0.0

# Switch back to non-root user
USER appuser

# Development command with reload
CMD ["uvicorn", "grc_backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
