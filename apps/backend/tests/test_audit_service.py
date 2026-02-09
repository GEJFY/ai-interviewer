"""監査サービスのユニットテスト。

テスト対象: apps/backend/src/grc_backend/services/audit_service.py
"""

import json
from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from grc_backend.services.audit_service import (
    AuditAction,
    AuditEvent,
    AuditService,
    AuditSeverity,
)


@pytest.fixture
def audit_service():
    """テスト用AuditServiceインスタンス。"""
    return AuditService()


# --- AuditAction / AuditSeverity テスト ---


class TestAuditEnums:
    """監査関連enumのテスト。"""

    def test_audit_actions_exist(self):
        """主要な監査アクションが定義されていること。"""
        assert AuditAction.LOGIN == "auth.login"
        assert AuditAction.PROJECT_CREATED == "project.created"
        assert AuditAction.INTERVIEW_STARTED == "interview.started"
        assert AuditAction.REPORT_GENERATED == "report.generated"

    def test_audit_severity_levels(self):
        """重要度レベルが定義されていること。"""
        assert AuditSeverity.INFO == "info"
        assert AuditSeverity.WARNING == "warning"
        assert AuditSeverity.CRITICAL == "critical"


# --- AuditService.log() テスト ---


class TestAuditServiceLog:
    """AuditService.log() のテスト。"""

    @pytest.mark.asyncio
    async def test_log_creates_event(self, audit_service):
        """ログがイベントを作成すること。"""
        event = await audit_service.log(
            action=AuditAction.LOGIN,
            user_email="test@example.com",
        )
        assert isinstance(event, AuditEvent)
        assert event.action == AuditAction.LOGIN
        assert event.user_email == "test@example.com"

    @pytest.mark.asyncio
    async def test_log_stores_event(self, audit_service):
        """ログがイベントを内部リストに格納すること。"""
        await audit_service.log(action=AuditAction.LOGIN)
        assert len(audit_service._events) == 1

    @pytest.mark.asyncio
    async def test_log_calls_handlers(self, audit_service):
        """ログがイベントハンドラーを呼び出すこと。"""
        received_events = []

        async def handler(event):
            received_events.append(event)

        audit_service.add_event_handler(handler)
        await audit_service.log(action=AuditAction.LOGIN)
        assert len(received_events) == 1

    @pytest.mark.asyncio
    async def test_log_handler_error_does_not_propagate(self, audit_service):
        """ハンドラーのエラーが伝搬しないこと。"""

        async def bad_handler(event):
            raise RuntimeError("ハンドラーエラー")

        audit_service.add_event_handler(bad_handler)
        # エラーが発生しても正常にイベントが返ること
        event = await audit_service.log(action=AuditAction.LOGIN)
        assert event is not None

    @pytest.mark.asyncio
    async def test_log_with_all_fields(self, audit_service):
        """全フィールド指定でイベントが正しく作成されること。"""
        user_id = uuid4()
        org_id = uuid4()
        event = await audit_service.log(
            action=AuditAction.PROJECT_CREATED,
            user_id=user_id,
            user_email="admin@example.com",
            resource_type="project",
            resource_id=uuid4(),
            details={"name": "テストプロジェクト"},
            ip_address="192.168.1.1",
            severity=AuditSeverity.INFO,
            success=True,
            organization_id=org_id,
        )
        assert event.user_id == user_id
        assert event.details["name"] == "テストプロジェクト"
        assert event.organization_id == org_id


# --- AuditService.query() テスト ---


class TestAuditServiceQuery:
    """AuditService.query() のテスト。"""

    @pytest.mark.asyncio
    async def test_query_filter_by_user_id(self, audit_service):
        """user_idでフィルタできること。"""
        uid1 = uuid4()
        uid2 = uuid4()
        await audit_service.log(action=AuditAction.LOGIN, user_id=uid1)
        await audit_service.log(action=AuditAction.LOGIN, user_id=uid2)

        results = await audit_service.query(user_id=uid1)
        assert len(results) == 1
        assert results[0].user_id == uid1

    @pytest.mark.asyncio
    async def test_query_filter_by_action(self, audit_service):
        """actionでフィルタできること。"""
        await audit_service.log(action=AuditAction.LOGIN)
        await audit_service.log(action=AuditAction.LOGOUT)
        await audit_service.log(action=AuditAction.LOGIN)

        results = await audit_service.query(action=AuditAction.LOGIN)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_query_filter_by_severity(self, audit_service):
        """severityでフィルタできること。"""
        await audit_service.log(action=AuditAction.LOGIN, severity=AuditSeverity.INFO)
        await audit_service.log(
            action=AuditAction.LOGIN_FAILED, severity=AuditSeverity.WARNING
        )

        results = await audit_service.query(severity=AuditSeverity.WARNING)
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_query_pagination(self, audit_service):
        """ページネーション(limit/offset)が動作すること。"""
        for _ in range(5):
            await audit_service.log(action=AuditAction.LOGIN)

        results = await audit_service.query(limit=2, offset=0)
        assert len(results) == 2

        results = await audit_service.query(limit=2, offset=3)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_query_returns_newest_first(self, audit_service):
        """新しいイベントが先に返ること。"""
        await audit_service.log(action=AuditAction.LOGIN, user_email="first")
        await audit_service.log(action=AuditAction.LOGIN, user_email="second")

        results = await audit_service.query()
        assert results[0].user_email == "second"


# --- AuditService.get_user_activity() テスト ---


class TestAuditServiceGetUserActivity:
    """AuditService.get_user_activity() のテスト。"""

    @pytest.mark.asyncio
    async def test_returns_summary_structure(self, audit_service):
        """サマリの構造が正しいこと。"""
        uid = uuid4()
        await audit_service.log(action=AuditAction.LOGIN, user_id=uid)
        await audit_service.log(action=AuditAction.PROJECT_CREATED, user_id=uid)

        summary = await audit_service.get_user_activity(uid)
        assert "user_id" in summary
        assert "total_actions" in summary
        assert "action_breakdown" in summary
        assert "failed_actions" in summary
        assert summary["total_actions"] == 2


# --- AuditService.export_logs() テスト ---


class TestAuditServiceExportLogs:
    """AuditService.export_logs() のテスト。"""

    @pytest.mark.asyncio
    async def test_export_json(self, audit_service):
        """JSON形式のエクスポートが正しいこと。"""
        await audit_service.log(action=AuditAction.LOGIN, user_email="test@example.com")

        now = datetime.utcnow()
        data = await audit_service.export_logs(
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=1),
            format="json",
        )
        parsed = json.loads(data.decode("utf-8"))
        assert isinstance(parsed, list)
        assert len(parsed) == 1

    @pytest.mark.asyncio
    async def test_export_csv(self, audit_service):
        """CSV形式のエクスポートが正しいこと。"""
        await audit_service.log(action=AuditAction.LOGIN, user_email="test@example.com")

        now = datetime.utcnow()
        data = await audit_service.export_logs(
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=1),
            format="csv",
        )
        csv_text = data.decode("utf-8")
        lines = csv_text.strip().split("\n")
        assert len(lines) == 2  # ヘッダー + 1行
        assert "timestamp" in lines[0]

    @pytest.mark.asyncio
    async def test_export_unsupported_format(self, audit_service):
        """非対応フォーマットでValueErrorが発生すること。"""
        now = datetime.utcnow()
        with pytest.raises(ValueError, match="Unsupported export format"):
            await audit_service.export_logs(
                start_time=now - timedelta(hours=1),
                end_time=now + timedelta(hours=1),
                format="xml",
            )


# --- イベントハンドラーテスト ---


class TestEventHandlers:
    """イベントハンドラーのライフサイクルテスト。"""

    def test_add_event_handler(self, audit_service):
        """ハンドラーが追加されること。"""

        async def handler(event):
            pass

        audit_service.add_event_handler(handler)
        assert handler in audit_service._event_handlers

    def test_remove_event_handler(self, audit_service):
        """ハンドラーが削除されること。"""

        async def handler(event):
            pass

        audit_service.add_event_handler(handler)
        audit_service.remove_event_handler(handler)
        assert handler not in audit_service._event_handlers

    def test_remove_nonexistent_handler(self, audit_service):
        """存在しないハンドラーの削除がエラーにならないこと。"""

        async def handler(event):
            pass

        # エラーが発生しないこと
        audit_service.remove_event_handler(handler)
