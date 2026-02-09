"""Enumeration definitions for the AI Interview Tool domain."""

from enum import StrEnum


class UserRole(StrEnum):
    """User roles for access control."""

    ADMIN = "admin"
    MANAGER = "manager"
    INTERVIEWER = "interviewer"
    VIEWER = "viewer"


class ProjectStatus(StrEnum):
    """Project lifecycle status."""

    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class TaskStatus(StrEnum):
    """Interview task status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class InterviewStatus(StrEnum):
    """Interview session status."""

    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Speaker(StrEnum):
    """Speaker identification for transcript entries."""

    AI = "ai"
    INTERVIEWEE = "interviewee"
    INTERVIEWER = "interviewer"


class ReportType(StrEnum):
    """Types of reports that can be generated."""

    SUMMARY = "summary"
    PROCESS_DOC = "process_doc"  # 業務記述書
    RCM = "rcm"  # リスクコントロールマトリクス
    AUDIT_WORKPAPER = "audit_workpaper"  # 監査調書
    SURVEY_ANALYSIS = "survey_analysis"  # 意識調査分析


class ReportStatus(StrEnum):
    """Report approval workflow status."""

    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    PUBLISHED = "published"


class UseCaseType(StrEnum):
    """GRC use case categories."""

    # Compliance
    COMPLIANCE_SURVEY = "compliance_survey"  # コンプライアンス意識調査
    WHISTLEBLOWER_INVESTIGATION = "whistleblower_investigation"  # 内部通報調査
    REGULATION_COMPLIANCE = "regulation_compliance"  # 規程遵守確認
    SUBCONTRACT_ACT = "subcontract_act"  # 下請法対応
    PRIVACY_ASSESSMENT = "privacy_assessment"  # 個人情報取扱
    BRIBERY_RISK = "bribery_risk"  # 贈収賄リスク

    # Internal Audit
    PROCESS_REVIEW = "process_review"  # 業務プロセスヒアリング
    TRANSACTION_VERIFICATION = "transaction_verification"  # 取引確認
    ANOMALY_INVESTIGATION = "anomaly_investigation"  # 異常取引調査
    CONTROL_EVALUATION = "control_evaluation"  # 統制評価（J-SOX）
    IT_CONTROL = "it_control"  # IT統制評価
    FOLLOWUP = "followup"  # フォローアップ

    # Risk Management
    RISK_ASSESSMENT = "risk_assessment"  # リスクアセスメント
    BCP_EVALUATION = "bcp_evaluation"  # BCP/BCM評価
    CYBER_RISK = "cyber_risk"  # サイバーリスク
    THIRD_PARTY_RISK = "third_party_risk"  # 第三者リスク
    ESG_RISK = "esg_risk"  # ESGリスク

    # Governance
    BOARD_EFFECTIVENESS = "board_effectiveness"  # 取締役会実効性
    INTERNAL_CONTROL_SYSTEM = "internal_control_system"  # 内部統制システム
    GROUP_GOVERNANCE = "group_governance"  # グループガバナンス

    # Knowledge Management
    TACIT_KNOWLEDGE = "tacit_knowledge"  # 暗黙知形式知化
    HANDOVER = "handover"  # 引継ぎ
    BEST_PRACTICE = "best_practice"  # ベストプラクティス
