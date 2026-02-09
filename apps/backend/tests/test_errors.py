"""エラーハンドリングモジュールのユニットテスト。

テスト対象: apps/backend/src/grc_backend/core/errors.py
"""

import pytest

from grc_backend.core.errors import (
    AIProviderError,
    AppError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    DatabaseError,
    ErrorCode,
    ErrorDetail,
    ExternalServiceError,
    NotFoundError,
    RateLimitError,
    RetryConfig,
    SpeechServiceError,
    StorageError,
    ValidationError,
)


# --- ErrorCode テスト ---


class TestErrorCode:
    """ErrorCode enum のテスト。"""

    def test_all_client_error_codes_exist(self):
        """全クライアントエラーコードが存在すること。"""
        expected = [
            "VALIDATION_ERROR",
            "AUTHENTICATION_REQUIRED",
            "INVALID_CREDENTIALS",
            "TOKEN_EXPIRED",
            "PERMISSION_DENIED",
            "RESOURCE_NOT_FOUND",
            "RESOURCE_CONFLICT",
            "RATE_LIMIT_EXCEEDED",
            "REQUEST_TOO_LARGE",
        ]
        for code in expected:
            assert hasattr(ErrorCode, code)

    def test_all_server_error_codes_exist(self):
        """全サーバーエラーコードが存在すること。"""
        expected = [
            "INTERNAL_ERROR",
            "SERVICE_UNAVAILABLE",
            "EXTERNAL_SERVICE_ERROR",
            "DATABASE_ERROR",
            "AI_PROVIDER_ERROR",
            "SPEECH_SERVICE_ERROR",
            "STORAGE_ERROR",
        ]
        for code in expected:
            assert hasattr(ErrorCode, code)

    def test_error_codes_are_string_values(self):
        """エラーコードが文字列値であること。"""
        for code in ErrorCode:
            assert isinstance(code.value, str)
            assert code.value == code.name


# --- AppError テスト ---


class TestAppError:
    """AppError のテスト。"""

    def test_to_dict_structure(self):
        """to_dict()の構造が正しいこと。"""
        error = AppError(message="テストエラー")
        result = error.to_dict()
        assert "error" in result
        assert result["error"]["code"] == "INTERNAL_ERROR"
        assert result["error"]["message"] == "テストエラー"
        assert "request_id" in result["error"]
        assert "timestamp" in result["error"]

    def test_to_dict_with_details(self):
        """detailsが含まれること。"""
        details = [ErrorDetail(field="email", message="必須項目です", code="required")]
        error = AppError(message="バリデーションエラー", details=details)
        result = error.to_dict()
        assert "details" in result["error"]
        assert len(result["error"]["details"]) == 1
        assert result["error"]["details"][0]["field"] == "email"

    def test_to_dict_without_details(self):
        """detailsが空の場合、レスポンスに含まれないこと。"""
        error = AppError(message="テストエラー")
        result = error.to_dict()
        assert "details" not in result["error"]

    def test_to_dict_with_retry_after(self):
        """retry_afterが含まれること。"""
        error = AppError(message="レート制限", retry_after=60)
        result = error.to_dict()
        assert result["error"]["retry_after"] == 60

    def test_to_dict_without_retry_after(self):
        """retry_afterが無い場合、レスポンスに含まれないこと。"""
        error = AppError(message="テストエラー")
        result = error.to_dict()
        assert "retry_after" not in result["error"]

    def test_to_dict_include_debug(self):
        """デバッグ情報が含まれること。"""
        cause = ValueError("原因のエラー")
        error = AppError(message="テスト", cause=cause)
        result = error.to_dict(include_debug=True)
        assert "debug" in result["error"]
        assert "原因のエラー" in result["error"]["debug"]["cause"]

    def test_to_dict_no_debug_without_cause(self):
        """causeなしの場合、デバッグ情報が含まれないこと。"""
        error = AppError(message="テスト")
        result = error.to_dict(include_debug=True)
        assert "debug" not in result["error"]

    def test_is_exception(self):
        """AppErrorがExceptionを継承していること。"""
        error = AppError(message="テスト")
        assert isinstance(error, Exception)


# --- 各エラー型テスト ---


class TestValidationError:
    """ValidationError のテスト。"""

    def test_default_values(self):
        """デフォルト値が正しいこと。"""
        error = ValidationError()
        assert error.code == ErrorCode.VALIDATION_ERROR
        assert error.status_code == 422
        assert error.message == "Validation failed"

    def test_custom_details(self):
        """カスタムdetailsが設定されること。"""
        details = [ErrorDetail(field="name", message="必須")]
        error = ValidationError(details=details)
        assert len(error.details) == 1


class TestAuthenticationError:
    """AuthenticationError のテスト。"""

    def test_default_values(self):
        """デフォルト値が正しいこと。"""
        error = AuthenticationError()
        assert error.code == ErrorCode.AUTHENTICATION_REQUIRED
        assert error.status_code == 401
        assert error.message == "Authentication required"

    def test_custom_code(self):
        """カスタムエラーコードが設定されること。"""
        error = AuthenticationError(code=ErrorCode.TOKEN_EXPIRED)
        assert error.code == ErrorCode.TOKEN_EXPIRED


class TestAuthorizationError:
    """AuthorizationError のテスト。"""

    def test_default_values(self):
        """デフォルト値とcontextが正しいこと。"""
        error = AuthorizationError(resource="project", action="delete")
        assert error.code == ErrorCode.PERMISSION_DENIED
        assert error.status_code == 403
        assert error.context["resource"] == "project"
        assert error.context["action"] == "delete"


class TestNotFoundError:
    """NotFoundError のテスト。"""

    def test_default_values(self):
        """デフォルト値とcontextが正しいこと。"""
        error = NotFoundError(resource_type="project", resource_id="abc-123")
        assert error.code == ErrorCode.RESOURCE_NOT_FOUND
        assert error.status_code == 404
        assert error.context["resource_type"] == "project"
        assert error.context["resource_id"] == "abc-123"


class TestConflictError:
    """ConflictError のテスト。"""

    def test_default_values(self):
        """デフォルト値が正しいこと。"""
        error = ConflictError()
        assert error.code == ErrorCode.RESOURCE_CONFLICT
        assert error.status_code == 409


class TestRateLimitError:
    """RateLimitError のテスト。"""

    def test_default_values(self):
        """デフォルト値が正しいこと。"""
        error = RateLimitError()
        assert error.code == ErrorCode.RATE_LIMIT_EXCEEDED
        assert error.status_code == 429
        assert error.retry_after == 60

    def test_custom_retry_after(self):
        """カスタムretry_afterが設定されること。"""
        error = RateLimitError(retry_after=120)
        assert error.retry_after == 120


class TestExternalServiceError:
    """ExternalServiceError のテスト。"""

    def test_default_values(self):
        """デフォルト値が正しいこと。"""
        error = ExternalServiceError(message="API失敗", service="openai")
        assert error.code == ErrorCode.EXTERNAL_SERVICE_ERROR
        assert error.status_code == 503
        assert error.context["service"] == "openai"


class TestAIProviderError:
    """AIProviderError のテスト。"""

    def test_inherits_external_service_error(self):
        """ExternalServiceErrorを継承していること。"""
        assert issubclass(AIProviderError, ExternalServiceError)

    def test_has_ai_provider_error_code(self):
        """AI_PROVIDER_ERRORコードが存在すること。"""
        assert ErrorCode.AI_PROVIDER_ERROR == "AI_PROVIDER_ERROR"


class TestSpeechServiceError:
    """SpeechServiceError のテスト。"""

    def test_inherits_external_service_error(self):
        """ExternalServiceErrorを継承していること。"""
        assert issubclass(SpeechServiceError, ExternalServiceError)

    def test_has_speech_service_error_code(self):
        """SPEECH_SERVICE_ERRORコードが存在すること。"""
        assert ErrorCode.SPEECH_SERVICE_ERROR == "SPEECH_SERVICE_ERROR"


class TestDatabaseError:
    """DatabaseError のテスト。"""

    def test_default_values(self):
        """デフォルト値が正しいこと。"""
        error = DatabaseError()
        assert error.code == ErrorCode.DATABASE_ERROR
        assert error.status_code == 500

    def test_operation_context(self):
        """operationがcontextに含まれること。"""
        error = DatabaseError(operation="INSERT")
        assert error.context["operation"] == "INSERT"


class TestStorageError:
    """StorageError のテスト。"""

    def test_inherits_external_service_error(self):
        """ExternalServiceErrorを継承していること。"""
        assert issubclass(StorageError, ExternalServiceError)


# --- RetryConfig テスト ---


class TestRetryConfig:
    """RetryConfig のテスト。"""

    def test_default_values(self):
        """デフォルト値が正しいこと。"""
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.initial_delay == 1.0
        assert config.max_delay == 30.0
        assert config.exponential_base == 2.0

    def test_get_delay_exponential_backoff(self):
        """指数バックオフが正しく計算されること。"""
        config = RetryConfig(initial_delay=1.0, exponential_base=2.0)
        assert config.get_delay(1) == 1.0   # 1.0 * 2^0
        assert config.get_delay(2) == 2.0   # 1.0 * 2^1
        assert config.get_delay(3) == 4.0   # 1.0 * 2^2

    def test_get_delay_respects_max_delay(self):
        """max_delayの上限が適用されること。"""
        config = RetryConfig(initial_delay=1.0, max_delay=5.0, exponential_base=2.0)
        assert config.get_delay(10) == 5.0  # 1.0 * 2^9 = 512 → 上限5.0
