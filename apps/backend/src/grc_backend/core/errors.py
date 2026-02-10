"""Enterprise-level error handling infrastructure.

Provides:
- Standardized error hierarchy
- Consistent error responses
- Error tracking and correlation
- Retry logic for transient failures
"""

from __future__ import annotations

import traceback
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from fastapi import Request, status
from fastapi.responses import JSONResponse

from .logging import get_logger, request_id_var

logger = get_logger(__name__)


class ErrorCode(StrEnum):
    """Standardized error codes for API responses."""

    # Client errors (4xx)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    REQUEST_TOO_LARGE = "REQUEST_TOO_LARGE"

    # Server errors (5xx)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    AI_PROVIDER_ERROR = "AI_PROVIDER_ERROR"
    SPEECH_SERVICE_ERROR = "SPEECH_SERVICE_ERROR"
    STORAGE_ERROR = "STORAGE_ERROR"


@dataclass
class ErrorDetail:
    """Detailed error information for debugging."""

    field: str | None = None
    message: str = ""
    code: str | None = None
    value: Any = None


@dataclass
class AppError(Exception):
    """Base application error with structured error information.

    All application errors should inherit from this class for
    consistent error handling and logging.
    """

    message: str
    code: ErrorCode = ErrorCode.INTERNAL_ERROR
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    details: list[ErrorDetail] = field(default_factory=list)
    cause: Exception | None = None
    retry_after: int | None = None  # Seconds until retry allowed
    context: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        super().__init__(self.message)
        self.timestamp = datetime.now(UTC)
        self.request_id = request_id_var.get("")

    def to_dict(self, include_debug: bool = False) -> dict[str, Any]:
        """Convert error to dictionary for JSON response."""
        response = {
            "error": {
                "code": self.code.value,
                "message": self.message,
                "request_id": self.request_id,
                "timestamp": self.timestamp.isoformat(),
            }
        }

        if self.details:
            response["error"]["details"] = [
                {"field": d.field, "message": d.message, "code": d.code} for d in self.details
            ]

        if self.retry_after:
            response["error"]["retry_after"] = self.retry_after

        if include_debug and self.cause:
            response["error"]["debug"] = {
                "cause": str(self.cause),
                "traceback": traceback.format_exception(
                    type(self.cause), self.cause, self.cause.__traceback__
                ),
            }

        return response


# Specific error types


class ValidationError(AppError):
    """Validation error for invalid input data."""

    def __init__(
        self,
        message: str = "Validation failed",
        details: list[ErrorDetail] | None = None,
        **kwargs,
    ):
        super().__init__(
            message=message,
            code=ErrorCode.VALIDATION_ERROR,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details or [],
            **kwargs,
        )


class AuthenticationError(AppError):
    """Authentication error for unauthenticated requests."""

    def __init__(
        self,
        message: str = "Authentication required",
        code: ErrorCode = ErrorCode.AUTHENTICATION_REQUIRED,
        **kwargs,
    ):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_401_UNAUTHORIZED,
            **kwargs,
        )


class AuthorizationError(AppError):
    """Authorization error for unauthorized access attempts."""

    def __init__(
        self,
        message: str = "Permission denied",
        resource: str | None = None,
        action: str | None = None,
        **kwargs,
    ):
        super().__init__(
            message=message,
            code=ErrorCode.PERMISSION_DENIED,
            status_code=status.HTTP_403_FORBIDDEN,
            context={"resource": resource, "action": action},
            **kwargs,
        )


class NotFoundError(AppError):
    """Resource not found error."""

    def __init__(
        self,
        message: str = "Resource not found",
        resource_type: str | None = None,
        resource_id: str | None = None,
        **kwargs,
    ):
        super().__init__(
            message=message,
            code=ErrorCode.RESOURCE_NOT_FOUND,
            status_code=status.HTTP_404_NOT_FOUND,
            context={"resource_type": resource_type, "resource_id": resource_id},
            **kwargs,
        )


class ConflictError(AppError):
    """Resource conflict error (duplicate, version mismatch, etc.)."""

    def __init__(
        self,
        message: str = "Resource conflict",
        resource_type: str | None = None,
        conflict_reason: str | None = None,
        **kwargs,
    ):
        super().__init__(
            message=message,
            code=ErrorCode.RESOURCE_CONFLICT,
            status_code=status.HTTP_409_CONFLICT,
            context={"resource_type": resource_type, "reason": conflict_reason},
            **kwargs,
        )


class RateLimitError(AppError):
    """Rate limit exceeded error."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int = 60,
        limit: int | None = None,
        window: str | None = None,
        **kwargs,
    ):
        super().__init__(
            message=message,
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            retry_after=retry_after,
            context={"limit": limit, "window": window},
            **kwargs,
        )


class ExternalServiceError(AppError):
    """External service error (AI, Speech, Storage, etc.)."""

    def __init__(
        self,
        message: str,
        service: str,
        code: ErrorCode = ErrorCode.EXTERNAL_SERVICE_ERROR,
        cause: Exception | None = None,
        retry_after: int | None = None,
        **kwargs,
    ):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            cause=cause,
            retry_after=retry_after,
            context={"service": service},
            **kwargs,
        )


class AIProviderError(ExternalServiceError):
    """AI provider error (OpenAI, Azure, AWS Bedrock, GCP Vertex)."""

    def __init__(
        self,
        message: str,
        provider: str,
        model: str | None = None,
        cause: Exception | None = None,
        **kwargs,
    ):
        super().__init__(
            message=message,
            service=f"AI/{provider}",
            code=ErrorCode.AI_PROVIDER_ERROR,
            cause=cause,
            context={"provider": provider, "model": model},
            **kwargs,
        )


class SpeechServiceError(ExternalServiceError):
    """Speech service error (STT/TTS)."""

    def __init__(
        self,
        message: str,
        service_type: str,  # "stt" or "tts"
        provider: str,
        cause: Exception | None = None,
        **kwargs,
    ):
        super().__init__(
            message=message,
            service=f"Speech/{provider}/{service_type}",
            code=ErrorCode.SPEECH_SERVICE_ERROR,
            cause=cause,
            context={"service_type": service_type, "provider": provider},
            **kwargs,
        )


class DatabaseError(AppError):
    """Database operation error."""

    def __init__(
        self,
        message: str = "Database operation failed",
        operation: str | None = None,
        cause: Exception | None = None,
        **kwargs,
    ):
        super().__init__(
            message=message,
            code=ErrorCode.DATABASE_ERROR,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            cause=cause,
            context={"operation": operation},
            **kwargs,
        )


class StorageError(ExternalServiceError):
    """Storage service error (Azure Blob, S3, GCS)."""

    def __init__(
        self,
        message: str,
        provider: str,
        operation: str | None = None,
        cause: Exception | None = None,
        **kwargs,
    ):
        super().__init__(
            message=message,
            service=f"Storage/{provider}",
            code=ErrorCode.STORAGE_ERROR,
            cause=cause,
            context={"operation": operation},
            **kwargs,
        )


# Error handler middleware


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Handle AppError exceptions and return structured JSON response."""
    # Log the error
    logger.error(
        f"Application error: {exc.code.value}",
        error_code=exc.code.value,
        status_code=exc.status_code,
        message=exc.message,
        context=exc.context,
        exc_info=exc.cause if exc.cause else None,
    )

    # Build response headers
    headers = {}
    if exc.retry_after:
        headers["Retry-After"] = str(exc.retry_after)

    # Return JSON response
    include_debug = request.app.state.debug if hasattr(request.app.state, "debug") else False

    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(include_debug=include_debug),
        headers=headers,
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions and return generic error response."""
    # Log the unexpected error
    logger.critical(
        "Unexpected error occurred",
        error_type=type(exc).__name__,
        message=str(exc),
        exc_info=exc,
    )

    # Return generic error response
    error = AppError(
        message="An unexpected error occurred",
        code=ErrorCode.INTERNAL_ERROR,
    )

    include_debug = request.app.state.debug if hasattr(request.app.state, "debug") else False

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error.to_dict(include_debug=include_debug),
    )


# Retry helper


class RetryConfig:
    """Configuration for retry logic."""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
        retryable_exceptions: tuple = (ExternalServiceError,),
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retryable_exceptions = retryable_exceptions

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for the given attempt number."""
        delay = self.initial_delay * (self.exponential_base ** (attempt - 1))
        return min(delay, self.max_delay)


async def retry_async(
    func,
    *args,
    config: RetryConfig | None = None,
    **kwargs,
):
    """Execute async function with retry logic.

    Args:
        func: Async function to execute
        config: Retry configuration
        *args, **kwargs: Arguments to pass to the function

    Returns:
        Function result

    Raises:
        Last exception if all retries fail
    """
    import asyncio

    config = config or RetryConfig()
    last_exception = None

    for attempt in range(1, config.max_attempts + 1):
        try:
            return await func(*args, **kwargs)
        except config.retryable_exceptions as e:
            last_exception = e
            if attempt < config.max_attempts:
                delay = config.get_delay(attempt)
                logger.warning(
                    f"Retry attempt {attempt}/{config.max_attempts} after {delay:.1f}s",
                    error=str(e),
                    attempt=attempt,
                    delay=delay,
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    f"All {config.max_attempts} retry attempts failed",
                    error=str(e),
                )

    raise last_exception
