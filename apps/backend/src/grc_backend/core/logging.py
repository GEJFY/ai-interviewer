"""Enterprise-level structured logging infrastructure.

Provides:
- JSON structured logging for log aggregation (CloudWatch, Azure Monitor, GCP Logging)
- Request correlation IDs for distributed tracing
- Sensitive data masking
- Performance metrics logging
- Audit trail integration
"""

import json
import logging
import sys
import time
import traceback
import uuid
from collections.abc import Callable
from contextvars import ContextVar
from datetime import UTC, datetime
from functools import wraps
from typing import Any

# Context variables for request tracking
request_id_var: ContextVar[str] = ContextVar("request_id", default="")
user_id_var: ContextVar[str] = ContextVar("user_id", default="")
session_id_var: ContextVar[str] = ContextVar("session_id", default="")


class LogContext:
    """Context manager for structured logging context."""

    def __init__(
        self,
        request_id: str | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
    ):
        self.request_id = request_id or str(uuid.uuid4())
        self.user_id = user_id or ""
        self.session_id = session_id or ""
        self._tokens: list = []

    def __enter__(self):
        self._tokens.append(request_id_var.set(self.request_id))
        if self.user_id:
            self._tokens.append(user_id_var.set(self.user_id))
        if self.session_id:
            self._tokens.append(session_id_var.set(self.session_id))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for token in self._tokens:
            try:
                if hasattr(token, "var"):
                    token.var.reset(token)
            except ValueError:
                pass


# Sensitive field patterns to mask in logs
SENSITIVE_FIELDS = {
    "password",
    "api_key",
    "secret",
    "token",
    "authorization",
    "cookie",
    "credential",
    "private_key",
    "access_token",
    "refresh_token",
    "api_secret",
    "client_secret",
}


def mask_sensitive_data(data: Any, depth: int = 0) -> Any:
    """Recursively mask sensitive data in log payloads."""
    if depth > 10:  # Prevent infinite recursion
        return "[DEPTH_LIMIT]"

    if isinstance(data, dict):
        masked = {}
        for key, value in data.items():
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in SENSITIVE_FIELDS):
                masked[key] = "[REDACTED]"
            else:
                masked[key] = mask_sensitive_data(value, depth + 1)
        return masked
    elif isinstance(data, list):
        return [mask_sensitive_data(item, depth + 1) for item in data]
    elif isinstance(data, str) and len(data) > 100:
        # Truncate very long strings in logs
        return data[:100] + "...[TRUNCATED]"
    return data


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def __init__(self, service_name: str = "ai-interviewer", environment: str = "development"):
        super().__init__()
        self.service_name = service_name
        self.environment = environment

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": self.service_name,
            "environment": self.environment,
            "request_id": request_id_var.get(""),
            "user_id": user_id_var.get(""),
            "session_id": session_id_var.get(""),
            "source": {
                "file": record.filename,
                "line": record.lineno,
                "function": record.funcName,
            },
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "stacktrace": traceback.format_exception(*record.exc_info),
            }

        # Add extra fields (masked)
        if hasattr(record, "extra_data"):
            log_entry["data"] = mask_sensitive_data(record.extra_data)

        # Add performance metrics if present
        if hasattr(record, "duration_ms"):
            log_entry["duration_ms"] = record.duration_ms

        return json.dumps(log_entry, ensure_ascii=False, default=str)


class ConsoleFormatter(logging.Formatter):
    """Human-readable console formatter for development."""

    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        request_id = request_id_var.get("")[:8] if request_id_var.get("") else ""

        prefix = f"{color}[{record.levelname}]{self.RESET}"
        timestamp = datetime.now().strftime("%H:%M:%S")
        location = f"{record.filename}:{record.lineno}"

        message = f"{prefix} {timestamp} [{request_id}] {record.getMessage()} ({location})"

        if record.exc_info:
            message += "\n" + "".join(traceback.format_exception(*record.exc_info))

        return message


class StructuredLogger(logging.Logger):
    """Extended logger with structured logging capabilities."""

    def _log_with_extra(
        self,
        level: int,
        msg: str,
        args: tuple,
        exc_info=None,
        extra: dict | None = None,
        **kwargs,
    ):
        if extra is None:
            extra = {}
        extra["extra_data"] = kwargs
        super()._log(level, msg, args, exc_info=exc_info, extra=extra)

    def debug(self, msg: str, *args, **kwargs):
        self._log_with_extra(logging.DEBUG, msg, args, **kwargs)

    def info(self, msg: str, *args, **kwargs):
        self._log_with_extra(logging.INFO, msg, args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        self._log_with_extra(logging.WARNING, msg, args, **kwargs)

    def error(self, msg: str, *args, exc_info=True, **kwargs):
        self._log_with_extra(logging.ERROR, msg, args, exc_info=exc_info, **kwargs)

    def critical(self, msg: str, *args, exc_info=True, **kwargs):
        self._log_with_extra(logging.CRITICAL, msg, args, exc_info=exc_info, **kwargs)

    def audit(self, action: str, resource_type: str, resource_id: str, **details):
        """Log an audit event."""
        self.info(
            f"AUDIT: {action} on {resource_type}",
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            audit=True,
            **details,
        )

    def performance(self, operation: str, duration_ms: float, **metrics):
        """Log performance metrics."""
        record = self.makeRecord(
            self.name,
            logging.INFO,
            "(unknown file)",
            0,
            f"PERF: {operation} completed in {duration_ms:.2f}ms",
            (),
            None,
        )
        record.duration_ms = duration_ms
        record.extra_data = {"operation": operation, **metrics}
        self.handle(record)


# Set custom logger class
logging.setLoggerClass(StructuredLogger)


def setup_logging(
    service_name: str = "ai-interviewer",
    environment: str = "development",
    log_level: str = "INFO",
    json_output: bool = False,
) -> None:
    """Configure application-wide logging.

    Args:
        service_name: Name of the service for log identification
        environment: Environment name (development, staging, production)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_output: Use JSON format (True for production, False for development)
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))

    if json_output or environment in ("staging", "production"):
        console_handler.setFormatter(JsonFormatter(service_name, environment))
    else:
        console_handler.setFormatter(ConsoleFormatter())

    root_logger.addHandler(console_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("azure").setLevel(logging.WARNING)
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        StructuredLogger instance
    """
    return logging.getLogger(name)  # type: ignore


def log_execution_time(operation_name: str | None = None):
    """Decorator to log function execution time.

    Args:
        operation_name: Custom operation name (defaults to function name)
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            op_name = operation_name or func.__name__
            start_time = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start_time) * 1000
                logger.performance(op_name, duration_ms, status="success")
                return result
            except Exception as e:
                duration_ms = (time.perf_counter() - start_time) * 1000
                logger.performance(op_name, duration_ms, status="error", error=str(e))
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            op_name = operation_name or func.__name__
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start_time) * 1000
                logger.performance(op_name, duration_ms, status="success")
                return result
            except Exception as e:
                duration_ms = (time.perf_counter() - start_time) * 1000
                logger.performance(op_name, duration_ms, status="error", error=str(e))
                raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


class RequestLogger:
    """Middleware for logging HTTP requests."""

    def __init__(self, logger: StructuredLogger):
        self.logger = logger

    async def log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        user_id: str | None = None,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ):
        """Log HTTP request details."""
        log_data = {
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "client_ip": client_ip,
            "user_agent": user_agent,
        }

        if status_code >= 500:
            self.logger.error(f"HTTP {method} {path} -> {status_code}", **log_data)
        elif status_code >= 400:
            self.logger.warning(f"HTTP {method} {path} -> {status_code}", **log_data)
        else:
            self.logger.info(f"HTTP {method} {path} -> {status_code}", **log_data)
