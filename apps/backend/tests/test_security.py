"""セキュリティモジュールのユニットテスト。

テスト対象: apps/backend/src/grc_backend/core/security.py
"""

import time
import unittest.mock
from unittest.mock import MagicMock

import pytest

from grc_backend.core.security import (
    APIKeyManager,
    CSRFProtection,
    RateLimiter,
    SecurityConfig,
)


# --- SecurityConfig テスト ---


class TestSecurityConfig:
    """SecurityConfig のテスト。"""

    def test_default_values(self):
        """デフォルト設定値が正しいこと。"""
        config = SecurityConfig()
        assert config.cors_origins == ["http://localhost:3100"]
        assert config.cors_allow_credentials is True
        assert config.rate_limit_enabled is True
        assert config.rate_limit_requests == 100
        assert config.rate_limit_window == 60
        assert config.ip_allowlist_enabled is False
        assert config.hsts_enabled is True
        assert config.max_request_size == 10 * 1024 * 1024
        assert config.debug is False

    def test_from_env_production(self):
        """production環境の設定が正しいこと。"""
        config = SecurityConfig.from_env("production")
        assert config.rate_limit_enabled is True
        assert config.rate_limit_requests == 60
        assert config.hsts_enabled is True
        assert config.csp_enabled is True
        assert config.debug is False

    def test_from_env_staging(self):
        """staging環境の設定が正しいこと。"""
        config = SecurityConfig.from_env("staging")
        assert config.rate_limit_enabled is True
        assert config.rate_limit_requests == 120
        assert config.debug is False
        assert "http://localhost:3100" in config.cors_origins

    def test_from_env_development(self):
        """development環境の設定が正しいこと。"""
        config = SecurityConfig.from_env("development")
        assert config.rate_limit_enabled is False
        assert config.hsts_enabled is False
        assert config.csp_enabled is False
        assert config.debug is True


# --- RateLimiter テスト ---


class TestRateLimiter:
    """RateLimiter のテスト。"""

    def test_allows_requests_within_limit(self):
        """制限内のリクエストが許可されること。"""
        limiter = RateLimiter(requests=5, window=60)
        allowed, info = limiter.is_allowed("test-key")
        assert allowed is True
        assert info["limit"] == 5
        assert info["remaining"] == 4

    def test_blocks_requests_exceeding_limit(self):
        """制限超過のリクエストが拒否されること。"""
        limiter = RateLimiter(requests=3, window=60)
        for _ in range(3):
            limiter.is_allowed("test-key")

        allowed, info = limiter.is_allowed("test-key")
        assert allowed is False
        assert info["remaining"] == 0

    def test_different_keys_tracked_independently(self):
        """異なるキーが独立して追跡されること。"""
        limiter = RateLimiter(requests=2, window=60)

        # key-a を2回消費
        limiter.is_allowed("key-a")
        limiter.is_allowed("key-a")
        allowed_a, _ = limiter.is_allowed("key-a")
        assert allowed_a is False

        # key-b はまだ使える
        allowed_b, _ = limiter.is_allowed("key-b")
        assert allowed_b is True

    def test_resets_after_window_expires(self):
        """ウィンドウ期限切れ後にリセットされること。"""
        limiter = RateLimiter(requests=1, window=1)  # 1秒ウィンドウ

        limiter.is_allowed("test-key")
        allowed_before, _ = limiter.is_allowed("test-key")
        assert allowed_before is False

        # ウィンドウ経過を待つ
        time.sleep(1.1)

        allowed_after, _ = limiter.is_allowed("test-key")
        assert allowed_after is True

    def test_remaining_decrements(self):
        """remainingが正しくデクリメントされること。"""
        limiter = RateLimiter(requests=3, window=60)
        _, info1 = limiter.is_allowed("key")
        assert info1["remaining"] == 2

        _, info2 = limiter.is_allowed("key")
        assert info2["remaining"] == 1

        _, info3 = limiter.is_allowed("key")
        assert info3["remaining"] == 0

    def test_info_contains_required_fields(self):
        """レート制限情報に必要なフィールドが含まれること。"""
        limiter = RateLimiter(requests=10, window=60)
        _, info = limiter.is_allowed("key")
        assert "limit" in info
        assert "remaining" in info
        assert "reset" in info
        assert "window" in info


# --- APIKeyManager テスト ---


class TestAPIKeyManager:
    """APIKeyManager のテスト。"""

    def test_generate_key_with_prefix(self):
        """プレフィックス付きのAPIキーが生成されること。"""
        manager = APIKeyManager("test-secret")
        raw_key, key_hash = manager.generate_key("grc")
        assert raw_key.startswith("grc_")
        assert len(raw_key) > 10

    def test_generate_key_produces_different_hash(self):
        """キーとハッシュが異なること。"""
        manager = APIKeyManager("test-secret")
        raw_key, key_hash = manager.generate_key()
        assert raw_key != key_hash

    def test_verify_correct_key(self):
        """正しいキーが検証を通ること。"""
        manager = APIKeyManager("test-secret")
        raw_key, key_hash = manager.generate_key()
        assert manager.verify_key(raw_key, key_hash) is True

    def test_verify_incorrect_key(self):
        """不正なキーが検証を通らないこと。"""
        manager = APIKeyManager("test-secret")
        _, key_hash = manager.generate_key()
        assert manager.verify_key("wrong-key", key_hash) is False

    def test_different_keys_produce_different_hashes(self):
        """異なるキーが異なるハッシュを生成すること。"""
        manager = APIKeyManager("test-secret")
        _, hash1 = manager.generate_key()
        _, hash2 = manager.generate_key()
        assert hash1 != hash2

    def test_custom_prefix(self):
        """カスタムプレフィックスが使用されること。"""
        manager = APIKeyManager("test-secret")
        raw_key, _ = manager.generate_key(prefix="custom")
        assert raw_key.startswith("custom_")


# --- CSRFProtection テスト ---


class TestCSRFProtection:
    """CSRFProtection のテスト。"""

    def test_generate_token_format(self):
        """トークンがtimestamp:signature形式であること。"""
        csrf = CSRFProtection("test-secret", token_lifetime=3600)
        token = csrf.generate_token("session-1")
        parts = token.split(":")
        assert len(parts) == 2
        # timestamp部分が数値であること
        int(parts[0])

    def test_validate_correct_token(self):
        """正しいトークンが検証を通ること。"""
        csrf = CSRFProtection("test-secret", token_lifetime=3600)
        token = csrf.generate_token("session-1")
        assert csrf.validate_token(token, "session-1") is True

    def test_validate_expired_token(self):
        """期限切れトークンが拒否されること。"""
        csrf = CSRFProtection("test-secret", token_lifetime=10)
        token = csrf.generate_token("session-1")
        # time.time()をモックして未来の時間を返す（sleepより確実）
        future_time = time.time() + 20
        with unittest.mock.patch(
            "grc_backend.core.security.time"
        ) as mock_time:
            mock_time.time.return_value = future_time
            assert csrf.validate_token(token, "session-1") is False

    def test_validate_invalid_signature(self):
        """不正な署名が拒否されること。"""
        csrf = CSRFProtection("test-secret", token_lifetime=3600)
        token = csrf.generate_token("session-1")
        timestamp = token.split(":")[0]
        tampered_token = f"{timestamp}:invalidsignature"
        assert csrf.validate_token(tampered_token, "session-1") is False

    def test_validate_malformed_token(self):
        """不正形式のトークンが拒否されること。"""
        csrf = CSRFProtection("test-secret", token_lifetime=3600)
        assert csrf.validate_token("no-colon-here", "session-1") is False
        assert csrf.validate_token("", "session-1") is False

    def test_different_sessions_different_tokens(self):
        """異なるセッションで異なるトークンが生成されること。"""
        csrf = CSRFProtection("test-secret", token_lifetime=3600)
        token1 = csrf.generate_token("session-1")
        token2 = csrf.generate_token("session-2")
        sig1 = token1.split(":")[1]
        sig2 = token2.split(":")[1]
        assert sig1 != sig2

    def test_wrong_session_id_rejected(self):
        """異なるセッションIDでのトークン検証が失敗すること。"""
        csrf = CSRFProtection("test-secret", token_lifetime=3600)
        token = csrf.generate_token("session-1")
        assert csrf.validate_token(token, "session-2") is False


# --- SecurityMiddleware テスト ---


class TestSecurityMiddlewareHelpers:
    """SecurityMiddlewareのヘルパーメソッドのテスト。"""

    def _create_middleware(self, config=None):
        """テスト用のMiddlewareインスタンスを作成。"""
        from grc_backend.core.security import SecurityMiddleware

        app = MagicMock()
        config = config or SecurityConfig()
        middleware = SecurityMiddleware.__new__(SecurityMiddleware)
        middleware.config = config
        middleware.rate_limiter = RateLimiter(
            requests=config.rate_limit_requests,
            window=config.rate_limit_window,
        )
        return middleware

    def test_get_client_ip_from_forwarded_for(self):
        """X-Forwarded-ForヘッダーからIPを取得できること。"""
        middleware = self._create_middleware()
        request = MagicMock()
        request.headers = {"X-Forwarded-For": "1.2.3.4, 5.6.7.8"}
        assert middleware._get_client_ip(request) == "1.2.3.4"

    def test_get_client_ip_from_real_ip(self):
        """X-Real-IPヘッダーからIPを取得できること。"""
        middleware = self._create_middleware()
        request = MagicMock()
        request.headers = {"X-Real-IP": "10.0.0.1"}
        assert middleware._get_client_ip(request) == "10.0.0.1"

    def test_get_client_ip_from_client(self):
        """直接接続のクライアントIPを取得できること。"""
        middleware = self._create_middleware()
        request = MagicMock()
        request.headers = {}
        request.client.host = "192.168.1.1"
        assert middleware._get_client_ip(request) == "192.168.1.1"

    def test_validate_ip_allows_normal_ip(self):
        """通常のIPが許可されること。"""
        middleware = self._create_middleware()
        assert middleware._validate_ip("1.2.3.4") is True

    def test_validate_ip_blocks_blocklisted_ip(self):
        """ブロックリストのIPが拒否されること。"""
        config = SecurityConfig(ip_blocklist=["1.2.3.4"])
        middleware = self._create_middleware(config)
        assert middleware._validate_ip("1.2.3.4") is False

    def test_validate_ip_blocks_network_range(self):
        """ブロックリストのネットワーク範囲内IPが拒否されること。"""
        config = SecurityConfig(ip_blocklist=["10.0.0.0/24"])
        middleware = self._create_middleware(config)
        assert middleware._validate_ip("10.0.0.5") is False
        assert middleware._validate_ip("10.0.1.5") is True

    def test_validate_ip_allowlist(self):
        """許可リスト有効時、リスト外のIPが拒否されること。"""
        config = SecurityConfig(
            ip_allowlist_enabled=True,
            ip_allowlist=["192.168.1.0/24"],
        )
        middleware = self._create_middleware(config)
        assert middleware._validate_ip("192.168.1.10") is True
        assert middleware._validate_ip("10.0.0.1") is False

    def test_validate_ip_unknown_allowed(self):
        """不明なIPが許可されること。"""
        middleware = self._create_middleware()
        assert middleware._validate_ip("unknown") is True
