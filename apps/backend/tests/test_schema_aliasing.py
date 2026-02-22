"""スキーマ camelCase エイリアスのユニットテスト。

テスト対象: packages/@grc/core/src/grc_core/schemas/base.py
"""

import pytest

from grc_core.enums import ReportType, UseCaseType
from grc_core.schemas.base import BaseSchema, PaginatedResponse


# --- camelCase エイリアス生成テスト ---


class TestBaseSchemaAliasing:
    """BaseSchema の alias_generator=to_camel テスト。"""

    def test_camel_case_serialization(self):
        """snake_case フィールドが camelCase でシリアライズされること。"""

        class SampleSchema(BaseSchema):
            first_name: str
            last_name: str
            is_active: bool

        obj = SampleSchema(first_name="太郎", last_name="山田", is_active=True)
        data = obj.model_dump(by_alias=True)
        assert "firstName" in data
        assert "lastName" in data
        assert "isActive" in data
        assert data["firstName"] == "太郎"

    def test_snake_case_also_accepted(self):
        """populate_by_name=True で snake_case 入力も受け付けること。"""

        class SampleSchema(BaseSchema):
            user_name: str
            email_address: str

        obj = SampleSchema(user_name="taro", email_address="taro@example.com")
        assert obj.user_name == "taro"
        assert obj.email_address == "taro@example.com"

    def test_camel_case_input_accepted(self):
        """camelCase 入力も受け付けること。"""

        class SampleSchema(BaseSchema):
            created_at: str
            updated_at: str

        obj = SampleSchema(createdAt="2025-01-01", updatedAt="2025-01-02")
        assert obj.created_at == "2025-01-01"
        assert obj.updated_at == "2025-01-02"

    def test_from_attributes(self):
        """from_attributes=True で ORM オブジェクトからの変換が可能であること。"""

        class SampleSchema(BaseSchema):
            task_count: int
            completed_task_count: int

        class FakeORM:
            task_count = 10
            completed_task_count = 5

        obj = SampleSchema.model_validate(FakeORM())
        assert obj.task_count == 10
        data = obj.model_dump(by_alias=True)
        assert data["taskCount"] == 10
        assert data["completedTaskCount"] == 5


class TestPaginatedResponse:
    """PaginatedResponse の camelCase テスト。"""

    def test_paginated_response_camel_case(self):
        """PaginatedResponse が camelCase でシリアライズされること。"""
        resp = PaginatedResponse[str](
            items=["a", "b"],
            total=2,
            page=1,
            page_size=10,
            pages=1,
        )
        data = resp.model_dump(by_alias=True)
        assert "pageSize" in data
        assert data["pageSize"] == 10
        assert data["items"] == ["a", "b"]


# --- ReportType enum テスト ---


class TestReportTypeEnum:
    """ReportType enum の新タイプ確認テスト。"""

    def test_all_report_types_exist(self):
        """全レポートタイプが定義されていること。"""
        expected = [
            "summary",
            "process_doc",
            "rcm",
            "audit_workpaper",
            "survey_analysis",
            "compliance_report",
            "risk_heatmap",
            "gap_analysis",
        ]
        actual = [rt.value for rt in ReportType]
        assert sorted(actual) == sorted(expected)

    def test_report_type_count(self):
        """ReportType が 8 種類であること。"""
        assert len(ReportType) == 8


# --- UseCaseType enum テスト ---


class TestUseCaseTypeEnum:
    """UseCaseType enum の確認テスト。"""

    def test_use_case_type_count(self):
        """UseCaseType が 23 種類であること。"""
        assert len(UseCaseType) == 23

    def test_compliance_types_exist(self):
        """コンプライアンス関連タイプが存在すること。"""
        assert UseCaseType.COMPLIANCE_SURVEY == "compliance_survey"
        assert UseCaseType.WHISTLEBLOWER_INVESTIGATION == "whistleblower_investigation"
        assert UseCaseType.BRIBERY_RISK == "bribery_risk"

    def test_governance_types_exist(self):
        """ガバナンス関連タイプが存在すること。"""
        assert UseCaseType.BOARD_EFFECTIVENESS == "board_effectiveness"
        assert UseCaseType.INTERNAL_CONTROL_SYSTEM == "internal_control_system"
        assert UseCaseType.GROUP_GOVERNANCE == "group_governance"

    def test_knowledge_types_exist(self):
        """ナレッジ管理タイプが存在すること。"""
        assert UseCaseType.TACIT_KNOWLEDGE == "tacit_knowledge"
        assert UseCaseType.HANDOVER == "handover"
        assert UseCaseType.BEST_PRACTICE == "best_practice"
