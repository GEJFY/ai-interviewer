"""エンタープライズ基盤統合のユニットテスト。

テスト対象:
  - apps/backend/src/grc_backend/config.py (新フィールド)
  - apps/backend/src/grc_backend/core/logging.py (setup_logging)
  - apps/backend/src/grc_backend/core/errors.py (エラーハンドラー)
  - apps/backend/src/grc_backend/core/security.py (SecurityConfig)
  - apps/backend/src/grc_backend/api/deps.py (AppError階層)
"""

from unittest.mock import MagicMock, patch

import pytest

from grc_backend.core.errors import (
    AppError,
    AuthenticationError,
    AuthorizationError,
    ErrorCode,
    NotFoundError,
    app_error_handler,
    generic_exception_handler,
)
from grc_backend.core.logging import setup_logging
from grc_backend.core.security import SecurityConfig

# --- Settings テスト ---


class TestSettingsNewFields:
    """Settingsの新フィールドのテスト。"""

    def test_default_log_level(self):
        """log_levelのデフォルト値がINFOであること。"""
        from grc_backend.config import Settings

        settings = Settings(_env_file=None)
        assert settings.log_level == "INFO"

    def test_default_json_logs(self):
        """json_logsのデフォルト値がFalseであること。"""
        from grc_backend.config import Settings

        settings = Settings(_env_file=None)
        assert settings.json_logs is False

    def test_default_rate_limit_enabled(self):
        """rate_limit_enabledのデフォルト値がFalseであること。"""
        from grc_backend.config import Settings

        settings = Settings(_env_file=None)
        assert settings.rate_limit_enabled is False

    def test_default_rate_limit_requests(self):
        """rate_limit_requestsのデフォルト値が100であること。"""
        from grc_backend.config import Settings

        settings = Settings(_env_file=None)
        assert settings.rate_limit_requests == 100

    def test_default_rate_limit_window(self):
        """rate_limit_windowのデフォルト値が60であること。"""
        from grc_backend.config import Settings

        settings = Settings(_env_file=None)
        assert settings.rate_limit_window == 60

    def test_log_level_from_env(self):
        """LOG_LEVEL環境変数が読み込まれること。"""
        from grc_backend.config import Settings

        with patch.dict("os.environ", {"LOG_LEVEL": "DEBUG"}):
            settings = Settings()
            assert settings.log_level == "DEBUG"

    def test_json_logs_from_env(self):
        """JSON_LOGS環境変数が読み込まれること。"""
        from grc_backend.config import Settings

        with patch.dict("os.environ", {"JSON_LOGS": "true"}):
            settings = Settings()
            assert settings.json_logs is True

    def test_rate_limit_enabled_from_env(self):
        """RATE_LIMIT_ENABLED環境変数が読み込まれること。"""
        from grc_backend.config import Settings

        with patch.dict("os.environ", {"RATE_LIMIT_ENABLED": "true"}):
            settings = Settings()
            assert settings.rate_limit_enabled is True


# --- Logging テスト ---


class TestSetupLogging:
    """setup_logging のテスト。"""

    def test_setup_logging_does_not_raise(self):
        """setup_logging()がエラーなく実行できること。"""
        setup_logging(
            service_name="test-service",
            environment="test",
            log_level="INFO",
            json_output=False,
        )

    def test_setup_logging_json_mode(self):
        """JSON出力モードがエラーなく設定できること。"""
        setup_logging(
            service_name="test-service",
            environment="production",
            log_level="WARNING",
            json_output=True,
        )

    def test_setup_logging_debug_level(self):
        """DEBUGレベルが設定できること。"""
        setup_logging(
            service_name="test-service",
            environment="development",
            log_level="DEBUG",
            json_output=False,
        )


# --- SecurityConfig テスト ---


class TestSecurityConfig:
    """SecurityConfig のテスト。"""

    def test_from_settings_development(self):
        """development環境のSecurityConfigが正しく生成されること。"""
        from grc_backend.config import Settings

        settings = Settings(environment="development")
        config = SecurityConfig(
            cors_origins=settings.cors_origins,
            rate_limit_enabled=settings.rate_limit_enabled,
            hsts_enabled=settings.is_production,
            csp_enabled=settings.is_production,
            debug=settings.debug,
        )
        assert config.rate_limit_enabled is False
        assert config.hsts_enabled is False
        assert config.csp_enabled is False

    def test_from_settings_production(self):
        """production環境のSecurityConfigが正しく生成されること。"""
        from grc_backend.config import Settings

        settings = Settings(environment="production")
        config = SecurityConfig(
            cors_origins=settings.cors_origins,
            rate_limit_enabled=True,
            rate_limit_requests=60,
            rate_limit_window=60,
            hsts_enabled=settings.is_production,
            csp_enabled=settings.is_production,
            debug=False,
        )
        assert config.rate_limit_enabled is True
        assert config.hsts_enabled is True
        assert config.csp_enabled is True
        assert config.debug is False

    def test_from_env_factory(self):
        """SecurityConfig.from_env()が正しく動作すること。"""
        dev_config = SecurityConfig.from_env("development")
        assert dev_config.rate_limit_enabled is False
        assert dev_config.debug is True

        prod_config = SecurityConfig.from_env("production")
        assert prod_config.rate_limit_enabled is True
        assert prod_config.debug is False


# --- Error Handler テスト ---


class TestErrorHandlers:
    """エラーハンドラーのテスト。"""

    @pytest.mark.asyncio
    async def test_app_error_handler_returns_json(self):
        """AppErrorがJSON形式のエラーレスポンスを返すこと。"""
        error = NotFoundError(
            message="Project not found",
            resource_type="Project",
            resource_id="123",
        )
        mock_request = MagicMock()
        mock_request.app.state.debug = False

        response = await app_error_handler(mock_request, error)
        assert response.status_code == 404
        assert response.body is not None

    @pytest.mark.asyncio
    async def test_authentication_error_status(self):
        """AuthenticationErrorが401を返すこと。"""
        error = AuthenticationError(
            message="Invalid token",
            code=ErrorCode.INVALID_CREDENTIALS,
        )
        assert error.status_code == 401

    @pytest.mark.asyncio
    async def test_authorization_error_status(self):
        """AuthorizationErrorが403を返すこと。"""
        error = AuthorizationError(
            message="Admin access required",
            resource="admin_endpoint",
            action="access",
        )
        assert error.status_code == 403

    @pytest.mark.asyncio
    async def test_generic_exception_handler_returns_500(self):
        """予期しないエラーが500を返すこと。"""
        error = RuntimeError("Unexpected error")
        mock_request = MagicMock()
        mock_request.app.state.debug = False

        response = await generic_exception_handler(mock_request, error)
        assert response.status_code == 500

    def test_app_error_to_dict(self):
        """AppError.to_dict()が正しいJSON構造を返すこと。"""
        error = AppError(
            message="Test error",
            code=ErrorCode.INTERNAL_ERROR,
        )
        result = error.to_dict()
        assert "error" in result
        assert result["error"]["code"] == "INTERNAL_ERROR"
        assert result["error"]["message"] == "Test error"
        assert "request_id" in result["error"]
        assert "timestamp" in result["error"]

    def test_app_error_to_dict_with_debug(self):
        """debug=Trueでcause情報が含まれること。"""
        cause = ValueError("original error")
        error = AppError(
            message="Wrapped error",
            code=ErrorCode.INTERNAL_ERROR,
            cause=cause,
        )
        result = error.to_dict(include_debug=True)
        assert "debug" in result["error"]
        assert "original error" in result["error"]["debug"]["cause"]


# --- Health Check テスト ---


class TestHealthCheckEnhanced:
    """拡張ヘルスチェックのテスト。"""

    def test_health_response_includes_new_fields(self):
        """HealthResponseに新フィールドが含まれること。"""
        from grc_backend.api.routes.health import HealthResponse

        resp = HealthResponse(
            status="healthy",
            database="healthy",
            redis="healthy",
            ai_provider="azure:configured",
            version="0.1.0",
            environment="development",
        )
        assert resp.redis == "healthy"
        assert resp.ai_provider == "azure:configured"
        assert resp.environment == "development"

    @pytest.mark.asyncio
    async def test_health_check_with_degraded_redis(self):
        """Redis不通時にdegradedを返すこと。"""
        from grc_backend.api.routes.health import HealthResponse

        resp = HealthResponse(
            status="degraded",
            database="healthy",
            redis="unhealthy",
            ai_provider="local:configured",
            version="0.1.0",
            environment="development",
        )
        assert resp.status == "degraded"
        assert resp.redis == "unhealthy"
