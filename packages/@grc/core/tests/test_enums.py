"""ドメインenumのユニットテスト。

テスト対象: packages/@grc/core/src/grc_core/enums.py
"""

from enum import StrEnum

import pytest

from grc_core.enums import (
    InterviewStatus,
    ProjectStatus,
    ReportStatus,
    ReportType,
    Speaker,
    TaskStatus,
    UseCaseType,
    UserRole,
)


class TestUserRole:
    """UserRole のテスト。"""

    def test_all_values(self):
        """全ロールが定義されていること。"""
        assert UserRole.ADMIN == "admin"
        assert UserRole.MANAGER == "manager"
        assert UserRole.INTERVIEWER == "interviewer"
        assert UserRole.VIEWER == "viewer"

    def test_count(self):
        assert len(UserRole) == 4


class TestProjectStatus:
    """ProjectStatus のテスト。"""

    def test_all_values(self):
        assert ProjectStatus.ACTIVE == "active"
        assert ProjectStatus.COMPLETED == "completed"
        assert ProjectStatus.ARCHIVED == "archived"

    def test_count(self):
        assert len(ProjectStatus) == 3


class TestTaskStatus:
    """TaskStatus のテスト。"""

    def test_all_values(self):
        assert TaskStatus.PENDING == "pending"
        assert TaskStatus.IN_PROGRESS == "in_progress"
        assert TaskStatus.COMPLETED == "completed"
        assert TaskStatus.CANCELLED == "cancelled"

    def test_count(self):
        assert len(TaskStatus) == 4


class TestInterviewStatus:
    """InterviewStatus のテスト。"""

    def test_all_values(self):
        assert InterviewStatus.SCHEDULED == "scheduled"
        assert InterviewStatus.IN_PROGRESS == "in_progress"
        assert InterviewStatus.PAUSED == "paused"
        assert InterviewStatus.COMPLETED == "completed"
        assert InterviewStatus.CANCELLED == "cancelled"

    def test_count(self):
        assert len(InterviewStatus) == 5


class TestSpeaker:
    """Speaker のテスト。"""

    def test_all_values(self):
        assert Speaker.AI == "ai"
        assert Speaker.INTERVIEWEE == "interviewee"
        assert Speaker.INTERVIEWER == "interviewer"

    def test_count(self):
        assert len(Speaker) == 3


class TestReportType:
    """ReportType のテスト。"""

    def test_all_values(self):
        assert ReportType.SUMMARY == "summary"
        assert ReportType.PROCESS_DOC == "process_doc"
        assert ReportType.RCM == "rcm"
        assert ReportType.AUDIT_WORKPAPER == "audit_workpaper"
        assert ReportType.SURVEY_ANALYSIS == "survey_analysis"

    def test_count(self):
        assert len(ReportType) == 5


class TestReportStatus:
    """ReportStatus のテスト。"""

    def test_all_values(self):
        assert ReportStatus.DRAFT == "draft"
        assert ReportStatus.REVIEW == "review"
        assert ReportStatus.APPROVED == "approved"
        assert ReportStatus.PUBLISHED == "published"

    def test_count(self):
        assert len(ReportStatus) == 4


class TestUseCaseType:
    """UseCaseType のテスト。"""

    def test_compliance_cases(self):
        """コンプライアンスカテゴリが存在すること。"""
        assert UseCaseType.COMPLIANCE_SURVEY == "compliance_survey"
        assert UseCaseType.WHISTLEBLOWER_INVESTIGATION == "whistleblower_investigation"
        assert UseCaseType.PRIVACY_ASSESSMENT == "privacy_assessment"

    def test_audit_cases(self):
        """内部監査カテゴリが存在すること。"""
        assert UseCaseType.PROCESS_REVIEW == "process_review"
        assert UseCaseType.CONTROL_EVALUATION == "control_evaluation"
        assert UseCaseType.IT_CONTROL == "it_control"

    def test_risk_cases(self):
        """リスク管理カテゴリが存在すること。"""
        assert UseCaseType.RISK_ASSESSMENT == "risk_assessment"
        assert UseCaseType.CYBER_RISK == "cyber_risk"
        assert UseCaseType.ESG_RISK == "esg_risk"

    def test_total_count(self):
        """全カテゴリが23以上あること。"""
        assert len(UseCaseType) >= 23


class TestAllEnumsAreStrEnum:
    """全enumがStrEnumであることのテスト。"""

    @pytest.mark.parametrize(
        "enum_cls",
        [
            UserRole,
            ProjectStatus,
            TaskStatus,
            InterviewStatus,
            Speaker,
            ReportType,
            ReportStatus,
            UseCaseType,
        ],
    )
    def test_is_str_enum(self, enum_cls):
        """StrEnumを継承していること。"""
        assert issubclass(enum_cls, StrEnum)

    @pytest.mark.parametrize(
        "enum_cls",
        [
            UserRole,
            ProjectStatus,
            TaskStatus,
            InterviewStatus,
            Speaker,
            ReportType,
            ReportStatus,
        ],
    )
    def test_values_are_strings(self, enum_cls):
        """全値がstr型であること。"""
        for member in enum_cls:
            assert isinstance(member.value, str)
