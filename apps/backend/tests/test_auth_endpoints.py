"""認証管理エンドポイントのユニットテスト。

テスト対象:
  - POST /auth/change-password
  - GET /auth/admin/users
  - POST /auth/admin/reset-password

注: 実際のHTTPテストではなく、Pydantic モデルとビジネスロジック関数をテストする。
"""

import pytest
from pydantic import ValidationError

from grc_backend.api.routes.auth import (
    AdminResetPasswordRequest,
    ChangePasswordRequest,
    get_password_hash,
    verify_password,
)


# --- ChangePasswordRequest モデルテスト ---


class TestChangePasswordRequest:
    """ChangePasswordRequest Pydantic モデルのテスト。"""

    def test_valid_request(self):
        """正しいリクエストが受理されること。"""
        req = ChangePasswordRequest(
            current_password="oldpass123",
            new_password="newpass456",
        )
        assert req.current_password == "oldpass123"
        assert req.new_password == "newpass456"

    def test_missing_current_password(self):
        """current_password がない場合にバリデーションエラーになること。"""
        with pytest.raises(ValidationError):
            ChangePasswordRequest(new_password="newpass456")

    def test_missing_new_password(self):
        """new_password がない場合にバリデーションエラーになること。"""
        with pytest.raises(ValidationError):
            ChangePasswordRequest(current_password="oldpass123")


# --- AdminResetPasswordRequest モデルテスト ---


class TestAdminResetPasswordRequest:
    """AdminResetPasswordRequest Pydantic モデルのテスト。"""

    def test_valid_request(self):
        """正しいリクエストが受理されること。"""
        req = AdminResetPasswordRequest(
            user_id="user-123",
            new_password="newpass789",
        )
        assert req.user_id == "user-123"
        assert req.new_password == "newpass789"

    def test_missing_user_id(self):
        """user_id がない場合にバリデーションエラーになること。"""
        with pytest.raises(ValidationError):
            AdminResetPasswordRequest(new_password="newpass789")

    def test_missing_new_password(self):
        """new_password がない場合にバリデーションエラーになること。"""
        with pytest.raises(ValidationError):
            AdminResetPasswordRequest(user_id="user-123")


# --- パスワード変更ロジックテスト ---


class TestPasswordChangeLogic:
    """パスワード変更のビジネスロジックテスト。"""

    def test_verify_current_password_success(self):
        """正しい現在のパスワードが検証を通ること。"""
        hashed = get_password_hash("current_password")
        assert verify_password("current_password", hashed) is True

    def test_verify_current_password_failure(self):
        """間違った現在のパスワードが拒否されること。"""
        hashed = get_password_hash("current_password")
        assert verify_password("wrong_password", hashed) is False

    def test_new_password_hash_different(self):
        """新しいパスワードが正しくハッシュされること。"""
        new_hash = get_password_hash("new_strong_password")
        assert verify_password("new_strong_password", new_hash) is True
        assert new_hash != "new_strong_password"

    def test_password_min_length_validation(self):
        """8文字未満のパスワードでもモデルレベルでは受理される（HTTPレイヤーで検証）。"""
        req = ChangePasswordRequest(
            current_password="old",
            new_password="short",
        )
        assert len(req.new_password) < 8

    def test_empty_password_still_hashable(self):
        """空文字でもハッシュ化は可能（バリデーションは別レイヤー）。"""
        hashed = get_password_hash("")
        assert verify_password("", hashed) is True
