"""OpenTelemetry integration for observability.

Opt-in via OTEL_ENABLED=true. Supports:
- Azure Application Insights (APPLICATIONINSIGHTS_CONNECTION_STRING)
- OTLP exporter (OTEL_EXPORTER_OTLP_ENDPOINT)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = logging.getLogger(__name__)


def setup_telemetry(
    app: FastAPI,
    *,
    service_name: str = "ai-interviewer",
    environment: str = "development",
    otel_enabled: bool = False,
    appinsights_connection_string: str = "",
) -> None:
    """Configure OpenTelemetry tracing for the FastAPI application.

    Args:
        app: FastAPI application instance
        service_name: Service name for traces
        environment: Deployment environment
        otel_enabled: Whether to enable telemetry
        appinsights_connection_string: Azure Application Insights connection string
    """
    if not otel_enabled:
        return

    try:
        from opentelemetry import trace
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        logger.warning("OpenTelemetry packages not installed, skipping telemetry setup")
        return

    resource = Resource.create(
        {
            "service.name": service_name,
            "deployment.environment": environment,
        }
    )
    provider = TracerProvider(resource=resource)

    # Azure Application Insights exporter
    if appinsights_connection_string:
        try:
            from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter

            exporter = AzureMonitorTraceExporter(
                connection_string=appinsights_connection_string,
            )
            provider.add_span_processor(BatchSpanProcessor(exporter))
            logger.info("Application Insights trace exporter configured")
        except ImportError:
            logger.warning("azure-monitor-opentelemetry-exporter not installed")

    # OTLP exporter (for Jaeger, Grafana Tempo, etc.)
    import os

    otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if otlp_endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                OTLPSpanExporter,
            )

            exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
            provider.add_span_processor(BatchSpanProcessor(exporter))
            logger.info("OTLP trace exporter configured", extra={"endpoint": otlp_endpoint})
        except ImportError:
            logger.warning("opentelemetry-exporter-otlp not installed")

    trace.set_tracer_provider(provider)

    # Auto-instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)

    # Auto-instrument SQLAlchemy (database queries)
    try:
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

        SQLAlchemyInstrumentor().instrument()
        logger.info("SQLAlchemy auto-instrumentation enabled")
    except ImportError:
        logger.debug("opentelemetry-instrumentation-sqlalchemy not installed, skipping")

    # Auto-instrument Redis
    try:
        from opentelemetry.instrumentation.redis import RedisInstrumentor

        RedisInstrumentor().instrument()
        logger.info("Redis auto-instrumentation enabled")
    except ImportError:
        logger.debug("opentelemetry-instrumentation-redis not installed, skipping")

    # Auto-instrument httpx (outbound HTTP calls to AI providers, SSO, etc.)
    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        HTTPXClientInstrumentor().instrument()
        logger.info("httpx auto-instrumentation enabled")
    except ImportError:
        logger.debug("opentelemetry-instrumentation-httpx not installed, skipping")

    logger.info(
        "OpenTelemetry configured",
        extra={"service": service_name, "environment": environment},
    )
