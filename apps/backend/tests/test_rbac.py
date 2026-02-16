"""RBACロールチェックのユニットテスト。

テスト対象: apps/backend/src/grc_backend/api/deps.py
"""

from unittest.mock import MagicMock

import pytest

from grc_backend.api.deps import (
    require_admin,
    require_interviewer_or_above,
    require_manager_or_admin,
)
from grc_backend.core.errors import AuthorizationError


class TestRequireAdmin:
    """require_admin のテスト。"""

    @pytest.mark.asyncio
    async def test_allows_admin(self):
        """adminロールが許可されること。"""
        user = MagicMock()
        user.role = "admin"
        result = await require_admin(user)
        assert result == user

    @pytest.mark.asyncio
    async def test_rejects_manager(self):
        """managerロールが拒否されること。"""
        user = MagicMock()
        user.role = "manager"
        with pytest.raises(AuthorizationError):
            await require_admin(user)

    @pytest.mark.asyncio
    async def test_rejects_user(self):
        """userロールが拒否されること。"""
        user = MagicMock()
        user.role = "user"
        with pytest.raises(AuthorizationError):
            await require_admin(user)


class TestRequireManagerOrAdmin:
    """require_manager_or_admin のテスト。"""

    @pytest.mark.asyncio
    async def test_allows_admin(self):
        user = MagicMock()
        user.role = "admin"
        result = await require_manager_or_admin(user)
        assert result == user

    @pytest.mark.asyncio
    async def test_allows_manager(self):
        user = MagicMock()
        user.role = "manager"
        result = await require_manager_or_admin(user)
        assert result == user

    @pytest.mark.asyncio
    async def test_rejects_user(self):
        user = MagicMock()
        user.role = "user"
        with pytest.raises(AuthorizationError):
            await require_manager_or_admin(user)

    @pytest.mark.asyncio
    async def test_rejects_viewer(self):
        user = MagicMock()
        user.role = "viewer"
        with pytest.raises(AuthorizationError):
            await require_manager_or_admin(user)


class TestRequireInterviewerOrAbove:
    """require_interviewer_or_above のテスト。"""

    @pytest.mark.asyncio
    async def test_allows_admin(self):
        user = MagicMock()
        user.role = "admin"
        result = await require_interviewer_or_above(user)
        assert result == user

    @pytest.mark.asyncio
    async def test_allows_manager(self):
        user = MagicMock()
        user.role = "manager"
        result = await require_interviewer_or_above(user)
        assert result == user

    @pytest.mark.asyncio
    async def test_allows_interviewer(self):
        user = MagicMock()
        user.role = "interviewer"
        result = await require_interviewer_or_above(user)
        assert result == user

    @pytest.mark.asyncio
    async def test_allows_user(self):
        """userロール（interviewer相当）が許可されること。"""
        user = MagicMock()
        user.role = "user"
        result = await require_interviewer_or_above(user)
        assert result == user

    @pytest.mark.asyncio
    async def test_rejects_viewer(self):
        """viewerロールが拒否されること。"""
        user = MagicMock()
        user.role = "viewer"
        with pytest.raises(AuthorizationError):
            await require_interviewer_or_above(user)
