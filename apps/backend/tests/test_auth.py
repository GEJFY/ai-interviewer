"""認証モジュールのユニットテスト。

テスト対象: apps/backend/src/grc_backend/api/routes/auth.py
"""

from datetime import timedelta
from unittest.mock import MagicMock

import pytest
from jose import jwt
from pydantic import ValidationError

from grc_backend.api.routes.auth import (
    LoginRequest,
    Token,
    TokenRefresh,
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)


# --- パスワードハッシュテスト ---


class TestPasswordHashing:
    """パスワードハッシュのテスト。"""

    def test_verify_correct_password(self):
        """正しいパスワードが検証を通ること。"""
        hashed = get_password_hash("test_password")
        assert verify_password("test_password", hashed) is True

    def test_verify_incorrect_password(self):
        """不正なパスワードが拒否されること。"""
        hashed = get_password_hash("test_password")
        assert verify_password("wrong_password", hashed) is False

    def test_different_passwords_different_hashes(self):
        """異なるパスワードで異なるハッシュが生成されること。"""
        hash1 = get_password_hash("password1")
        hash2 = get_password_hash("password2")
        assert hash1 != hash2

    def test_same_password_different_hashes(self):
        """同じパスワードでも毎回異なるハッシュ（salt）が生成されること。"""
        hash1 = get_password_hash("same_password")
        hash2 = get_password_hash("same_password")
        assert hash1 != hash2  # bcryptはsaltが異なる


# --- JWT トークンテスト ---


def _mock_settings():
    """テスト用のSettings モック。"""
    settings = MagicMock()
    settings.secret_key = "test-secret-key-for-jwt"
    settings.jwt_algorithm = "HS256"
    settings.access_token_expire_minutes = 30
    settings.refresh_token_expire_days = 7
    return settings


class TestCreateAccessToken:
    """create_access_token のテスト。"""

    def test_creates_valid_jwt(self):
        """有効なJWTが生成されること。"""
        settings = _mock_settings()
        token = create_access_token(
            data={"sub": "user-123"},
            settings=settings,
        )
        # デコード可能であること
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        assert payload["sub"] == "user-123"

    def test_token_has_access_type(self):
        """トークンにtype=accessが含まれること。"""
        settings = _mock_settings()
        token = create_access_token(data={"sub": "user-123"}, settings=settings)
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        assert payload["type"] == "access"

    def test_token_has_expiration(self):
        """トークンに有効期限(exp)が含まれること。"""
        settings = _mock_settings()
        token = create_access_token(data={"sub": "user-123"}, settings=settings)
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        assert "exp" in payload

    def test_custom_expires_delta(self):
        """カスタムexpires_deltaが適用されること。"""
        settings = _mock_settings()
        token = create_access_token(
            data={"sub": "user-123"},
            settings=settings,
            expires_delta=timedelta(minutes=5),
        )
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        assert "exp" in payload


class TestCreateRefreshToken:
    """create_refresh_token のテスト。"""

    def test_creates_valid_jwt(self):
        """有効なJWTリフレッシュトークンが生成されること。"""
        settings = _mock_settings()
        token = create_refresh_token(data={"sub": "user-123"}, settings=settings)
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        assert payload["sub"] == "user-123"

    def test_token_has_refresh_type(self):
        """トークンにtype=refreshが含まれること。"""
        settings = _mock_settings()
        token = create_refresh_token(data={"sub": "user-123"}, settings=settings)
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        assert payload["type"] == "refresh"

    def test_token_has_sub_claim(self):
        """トークンにsubクレームが含まれること。"""
        settings = _mock_settings()
        token = create_refresh_token(data={"sub": "user-456"}, settings=settings)
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        assert payload["sub"] == "user-456"


# --- Pydantic モデルテスト ---


class TestTokenModel:
    """Token Pydanticモデルのテスト。"""

    def test_default_token_type(self):
        """デフォルトのtoken_typeがbearerであること。"""
        token = Token(access_token="abc", refresh_token="def")
        assert token.token_type == "bearer"

    def test_required_fields(self):
        """必須フィールドが検証されること。"""
        with pytest.raises(ValidationError):
            Token()  # access_token, refresh_tokenが必須


class TestLoginRequest:
    """LoginRequest Pydanticモデルのテスト。"""

    def test_valid_email(self):
        """正しいメールアドレスが受理されること。"""
        req = LoginRequest(email="user@example.com", password="pass123")
        assert req.email == "user@example.com"

    def test_invalid_email_rejected(self):
        """不正なメールアドレスが拒否されること。"""
        with pytest.raises(ValidationError):
            LoginRequest(email="not-an-email", password="pass123")


class TestTokenRefresh:
    """TokenRefresh Pydanticモデルのテスト。"""

    def test_required_refresh_token(self):
        """refresh_tokenが必須であること。"""
        with pytest.raises(ValidationError):
            TokenRefresh()

    def test_valid_refresh_token(self):
        """正しいrefresh_tokenが受理されること。"""
        tr = TokenRefresh(refresh_token="some-token")
        assert tr.refresh_token == "some-token"
