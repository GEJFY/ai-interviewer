"""Enterprise-level security infrastructure.

Provides:
- Security headers middleware
- CORS configuration
- Rate limiting
- Request validation
- IP allowlisting
- API key management
- CSRF protection
"""

import hashlib
import hmac
import ipaddress
import secrets
import time
from collections.abc import Callable
from dataclasses import dataclass, field

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .logging import LogContext, get_logger

logger = get_logger(__name__)


@dataclass
class SecurityConfig:
    """Security configuration for the application."""

    # CORS settings
    cors_origins: list[str] = field(default_factory=lambda: ["http://localhost:3100"])
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = field(default_factory=lambda: ["*"])
    cors_allow_headers: list[str] = field(default_factory=lambda: ["*"])

    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100  # Requests per window
    rate_limit_window: int = 60  # Window in seconds
    redis_url: str | None = None  # Redis URL for distributed rate limiting

    # IP filtering
    ip_allowlist_enabled: bool = False
    ip_allowlist: list[str] = field(default_factory=list)
    ip_blocklist: list[str] = field(default_factory=list)

    # Security headers
    hsts_enabled: bool = True
    hsts_max_age: int = 31536000  # 1 year
    csp_enabled: bool = True
    csp_policy: str = (
        "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    )

    # Request validation
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    allowed_content_types: list[str] = field(
        default_factory=lambda: [
            "application/json",
            "multipart/form-data",
            "application/x-www-form-urlencoded",
        ]
    )

    # Debug mode (disable in production!)
    debug: bool = False

    @classmethod
    def from_env(cls, env: str = "development") -> "SecurityConfig":
        """Create security config from environment.

        In production/staging the CORS origins are read from the
        ``CORS_ORIGINS`` environment variable (comma-separated list).
        Falls back to localhost when the variable is absent so that
        local development works out of the box.
        """
        import os

        cors_env = os.getenv("CORS_ORIGINS", "")
        cors_from_env = [o.strip() for o in cors_env.split(",") if o.strip()]
        redis_url = os.getenv("REDIS_URL") or None

        if env == "production":
            return cls(
                cors_origins=cors_from_env or ["https://localhost:3100"],
                rate_limit_enabled=True,
                rate_limit_requests=60,
                ip_allowlist_enabled=False,
                hsts_enabled=True,
                csp_enabled=True,
                debug=False,
                redis_url=redis_url,
            )
        elif env == "staging":
            return cls(
                cors_origins=cors_from_env or ["http://localhost:3100"],
                rate_limit_enabled=True,
                rate_limit_requests=120,
                debug=False,
                redis_url=redis_url,
            )
        else:  # development
            return cls(
                cors_origins=cors_from_env or ["http://localhost:3100", "http://127.0.0.1:3100"],
                rate_limit_enabled=False,
                hsts_enabled=False,
                csp_enabled=False,
                debug=True,
                redis_url=redis_url,
            )


class RateLimiter:
    """Rate limiter with Redis backend and in-memory fallback.

    Uses Redis sorted sets for distributed rate limiting when available.
    Falls back to in-memory sliding window when Redis is not configured.
    """

    def __init__(self, requests: int = 100, window: int = 60, redis_url: str | None = None):
        self.requests = requests
        self.window = window
        self._redis = None
        self._store: dict[str, list[float]] = {}

        if redis_url:
            try:
                import redis as redis_lib

                self._redis = redis_lib.Redis.from_url(redis_url, decode_responses=True)
                self._redis.ping()
                logger.info("Rate limiter using Redis backend")
            except Exception:
                self._redis = None
                logger.info("Redis unavailable, rate limiter using in-memory fallback")

    def is_allowed(self, key: str) -> tuple[bool, dict]:
        """Check if request is allowed under rate limit."""
        if self._redis:
            return self._is_allowed_redis(key)
        return self._is_allowed_memory(key)

    def _is_allowed_redis(self, key: str) -> tuple[bool, dict]:
        """Redis-backed sliding window using sorted sets."""
        current_time = time.time()
        redis_key = f"ratelimit:{key}"
        cutoff = current_time - self.window

        pipe = self._redis.pipeline()
        pipe.zremrangebyscore(redis_key, 0, cutoff)
        pipe.zcard(redis_key)
        pipe.execute()

        request_count = self._redis.zcard(redis_key)
        remaining = max(0, self.requests - request_count)

        info = {
            "limit": self.requests,
            "remaining": remaining,
            "reset": int(current_time + self.window),
            "window": self.window,
        }

        if request_count >= self.requests:
            return False, info

        pipe = self._redis.pipeline()
        pipe.zadd(redis_key, {str(current_time): current_time})
        pipe.expire(redis_key, self.window)
        pipe.execute()

        info["remaining"] = remaining - 1
        return True, info

    def _is_allowed_memory(self, key: str) -> tuple[bool, dict]:
        """In-memory sliding window fallback."""
        current_time = time.time()
        cutoff = current_time - self.window

        if key in self._store:
            self._store[key] = [t for t in self._store[key] if t > cutoff]
        else:
            self._store[key] = []

        request_count = len(self._store[key])
        remaining = max(0, self.requests - request_count)

        info = {
            "limit": self.requests,
            "remaining": remaining,
            "reset": int(current_time + self.window),
            "window": self.window,
        }

        if request_count >= self.requests:
            return False, info

        self._store[key].append(current_time)
        info["remaining"] = remaining - 1
        return True, info


class SecurityMiddleware(BaseHTTPMiddleware):
    """Comprehensive security middleware."""

    def __init__(self, app: FastAPI, config: SecurityConfig):
        super().__init__(app)
        self.config = config
        self.rate_limiter = RateLimiter(
            requests=config.rate_limit_requests,
            window=config.rate_limit_window,
            redis_url=config.redis_url,
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = request.headers.get("X-Request-ID") or secrets.token_hex(16)

        # Set up logging context
        with LogContext(request_id=request_id):
            start_time = time.perf_counter()

            try:
                # IP validation
                client_ip = self._get_client_ip(request)
                if not self._validate_ip(client_ip):
                    return self._forbidden_response("IP address not allowed")

                # Rate limiting
                if self.config.rate_limit_enabled:
                    rate_key = f"{client_ip}:{request.url.path}"
                    allowed, rate_info = self.rate_limiter.is_allowed(rate_key)

                    if not allowed:
                        return self._rate_limit_response(rate_info)

                # Request size validation
                content_length = request.headers.get("content-length")
                if content_length and int(content_length) > self.config.max_request_size:
                    return self._payload_too_large_response()

                # Process request
                response = await call_next(request)

                # Add security headers
                self._add_security_headers(response, request_id)

                # Add rate limit headers
                if self.config.rate_limit_enabled:
                    response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
                    response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
                    response.headers["X-RateLimit-Reset"] = str(rate_info["reset"])

                # Log request
                duration_ms = (time.perf_counter() - start_time) * 1000
                logger.info(
                    f"{request.method} {request.url.path} -> {response.status_code}",
                    method=request.method,
                    path=str(request.url.path),
                    status_code=response.status_code,
                    duration_ms=round(duration_ms, 2),
                    client_ip=client_ip,
                    user_agent=request.headers.get("user-agent", "")[:100],
                )

                return response

            except Exception as e:
                logger.error(
                    "Security middleware error",
                    error=str(e),
                    exc_info=True,
                )
                raise

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request, handling proxies."""
        # Check X-Forwarded-For header (from load balancer/proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Take the first IP in the chain (original client)
            return forwarded.split(",")[0].strip()

        # Check X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        # Fall back to direct client IP
        if request.client:
            return request.client.host

        return "unknown"

    def _validate_ip(self, ip: str) -> bool:
        """Validate client IP against allowlist/blocklist."""
        if ip == "unknown":
            return True  # Allow if we can't determine IP

        try:
            client_ip = ipaddress.ip_address(ip)

            # Check blocklist first
            for blocked in self.config.ip_blocklist:
                try:
                    if "/" in blocked:
                        if client_ip in ipaddress.ip_network(blocked, strict=False):
                            logger.warning(f"Blocked IP: {ip}")
                            return False
                    elif client_ip == ipaddress.ip_address(blocked):
                        logger.warning(f"Blocked IP: {ip}")
                        return False
                except ValueError:
                    continue

            # Check allowlist if enabled
            if self.config.ip_allowlist_enabled and self.config.ip_allowlist:
                for allowed in self.config.ip_allowlist:
                    try:
                        if "/" in allowed:
                            if client_ip in ipaddress.ip_network(allowed, strict=False):
                                return True
                        elif client_ip == ipaddress.ip_address(allowed):
                            return True
                    except ValueError:
                        continue
                return False

        except ValueError:
            logger.warning(f"Invalid IP address: {ip}")
            return True  # Allow invalid IPs to not break the app

        return True

    def _add_security_headers(self, response: Response, request_id: str):
        """Add security headers to response."""
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        if self.config.hsts_enabled:
            response.headers["Strict-Transport-Security"] = (
                f"max-age={self.config.hsts_max_age}; includeSubDomains"
            )

        if self.config.csp_enabled:
            response.headers["Content-Security-Policy"] = self.config.csp_policy

    def _forbidden_response(self, message: str) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"error": {"code": "FORBIDDEN", "message": message}},
        )

    def _rate_limit_response(self, rate_info: dict) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests",
                    "retry_after": rate_info["window"],
                }
            },
            headers={
                "Retry-After": str(rate_info["window"]),
                "X-RateLimit-Limit": str(rate_info["limit"]),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(rate_info["reset"]),
            },
        )

    def _payload_too_large_response(self) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={
                "error": {
                    "code": "PAYLOAD_TOO_LARGE",
                    "message": f"Request body too large. Maximum size: {self.config.max_request_size} bytes",
                }
            },
        )


def setup_security(app: FastAPI, config: SecurityConfig | None = None) -> None:
    """Configure security middleware for the application.

    Args:
        app: FastAPI application instance
        config: Security configuration (uses defaults if not provided)
    """
    config = config or SecurityConfig()

    # Store debug mode in app state
    app.state.debug = config.debug

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=config.cors_allow_credentials,
        allow_methods=config.cors_allow_methods,
        allow_headers=config.cors_allow_headers,
    )

    # Add security middleware
    app.add_middleware(SecurityMiddleware, config=config)

    logger.info(
        "Security middleware configured",
        cors_origins=config.cors_origins,
        rate_limit_enabled=config.rate_limit_enabled,
        hsts_enabled=config.hsts_enabled,
    )


# API Key management


class APIKeyManager:
    """Manage API keys with hashing and validation."""

    def __init__(self, secret_key: str):
        self.secret_key = secret_key.encode()

    def generate_key(self, prefix: str = "grc") -> tuple[str, str]:
        """Generate a new API key and its hash.

        Returns:
            Tuple of (raw_key, key_hash)
        """
        raw_key = f"{prefix}_{secrets.token_urlsafe(32)}"
        key_hash = self._hash_key(raw_key)
        return raw_key, key_hash

    def _hash_key(self, key: str) -> str:
        """Create a secure hash of an API key."""
        return hmac.new(
            self.secret_key,
            key.encode(),
            hashlib.sha256,
        ).hexdigest()

    def verify_key(self, raw_key: str, stored_hash: str) -> bool:
        """Verify an API key against its stored hash."""
        computed_hash = self._hash_key(raw_key)
        return hmac.compare_digest(computed_hash, stored_hash)


# CSRF Token management


class CSRFProtection:
    """CSRF token generation and validation."""

    def __init__(self, secret_key: str, token_lifetime: int = 3600):
        self.secret_key = secret_key.encode()
        self.token_lifetime = token_lifetime

    def generate_token(self, session_id: str) -> str:
        """Generate a CSRF token tied to a session."""
        timestamp = str(int(time.time()))
        message = f"{session_id}:{timestamp}"
        signature = hmac.new(
            self.secret_key,
            message.encode(),
            hashlib.sha256,
        ).hexdigest()[:16]
        return f"{timestamp}:{signature}"

    def validate_token(self, token: str, session_id: str) -> bool:
        """Validate a CSRF token."""
        try:
            timestamp, signature = token.split(":")
            current_time = int(time.time())

            # Check token age
            if current_time - int(timestamp) > self.token_lifetime:
                return False

            # Verify signature
            expected_message = f"{session_id}:{timestamp}"
            expected_signature = hmac.new(
                self.secret_key,
                expected_message.encode(),
                hashlib.sha256,
            ).hexdigest()[:16]

            return hmac.compare_digest(signature, expected_signature)

        except (ValueError, AttributeError):
            return False
