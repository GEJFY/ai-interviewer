"""Tests for ReportGeneratorService.

ReportGeneratorService のレポート生成・エクスポート機能をテストする。
AI プロバイダーなし (mock content) のパスと、モック AI プロバイダーの両方を検証。
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from grc_backend.services.report_generator import (
    ExportFormat,
    GeneratedReport,
    ReportGeneratorService,
    ReportType,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def service():
    """ReportGeneratorService without AI provider (mock content)."""
    return ReportGeneratorService(ai_provider=None)


@pytest.fixture
def mock_ai_provider():
    """Mock AI provider that returns JSON."""
    provider = MagicMock()
    provider.chat = AsyncMock()
    return provider


@pytest.fixture
def service_with_ai(mock_ai_provider):
    """ReportGeneratorService with mock AI provider."""
    return ReportGeneratorService(ai_provider=mock_ai_provider)


@pytest.fixture
def sample_transcript():
    return "経理部マネージャーへのインタビューを実施。月次決算プロセスについてヒアリングした。"


@pytest.fixture
def sample_report():
    """Pre-built GeneratedReport for export tests."""
    return GeneratedReport(
        report_type=ReportType.SUMMARY,
        title="インタビュー要約",
        generated_at=datetime.utcnow(),
        content={
            "title": "インタビュー要約",
            "summary": "月次決算プロセスの詳細についてヒアリングを実施。",
            "key_findings": [
                {
                    "topic": "月次決算",
                    "finding": "手作業による照合作業が多い",
                    "significance": "中",
                }
            ],
            "follow_up_items": ["システム自動化の検討"],
            "date": "2026-02-16",
        },
        metadata={"interview_id": str(uuid4())},
    )


# ---------------------------------------------------------------------------
# ReportType / ExportFormat enums
# ---------------------------------------------------------------------------


class TestEnums:
    def test_report_types(self):
        assert ReportType.SUMMARY == "summary"
        assert ReportType.PROCESS_DOC == "process_doc"
        assert ReportType.RCM == "rcm"
        assert ReportType.AUDIT_WORKPAPER == "audit_workpaper"

    def test_export_formats(self):
        assert ExportFormat.JSON == "json"
        assert ExportFormat.MARKDOWN == "markdown"
        assert ExportFormat.WORD == "word"
        assert ExportFormat.EXCEL == "excel"
        assert ExportFormat.PDF == "pdf"


# ---------------------------------------------------------------------------
# generate_report (mock content path)
# ---------------------------------------------------------------------------


class TestGenerateReportMock:
    @pytest.mark.asyncio
    async def test_generate_summary(self, service, sample_transcript):
        report = await service.generate_report(
            interview_id=uuid4(),
            transcript=sample_transcript,
            report_type=ReportType.SUMMARY,
        )
        assert report.report_type == ReportType.SUMMARY
        assert report.title == "インタビュー要約"
        assert "key_findings" in report.content
        assert "summary" in report.content

    @pytest.mark.asyncio
    async def test_generate_process_doc(self, service, sample_transcript):
        report = await service.generate_report(
            interview_id=uuid4(),
            transcript=sample_transcript,
            report_type=ReportType.PROCESS_DOC,
        )
        assert report.report_type == ReportType.PROCESS_DOC
        assert report.title == "業務記述書"
        assert "process_steps" in report.content

    @pytest.mark.asyncio
    async def test_generate_rcm(self, service, sample_transcript):
        report = await service.generate_report(
            interview_id=uuid4(),
            transcript=sample_transcript,
            report_type=ReportType.RCM,
        )
        assert report.report_type == ReportType.RCM
        assert report.title == "リスクコントロールマトリックス"
        assert "items" in report.content

    @pytest.mark.asyncio
    async def test_generate_audit_workpaper(self, service, sample_transcript):
        report = await service.generate_report(
            interview_id=uuid4(),
            transcript=sample_transcript,
            report_type=ReportType.AUDIT_WORKPAPER,
        )
        assert report.report_type == ReportType.AUDIT_WORKPAPER
        assert report.title == "監査調書"
        assert "findings" in report.content
        assert "conclusion" in report.content

    @pytest.mark.asyncio
    async def test_metadata_contains_interview_id(self, service, sample_transcript):
        interview_id = uuid4()
        report = await service.generate_report(
            interview_id=interview_id,
            transcript=sample_transcript,
            report_type=ReportType.SUMMARY,
        )
        assert report.metadata["interview_id"] == str(interview_id)
        assert report.metadata["transcript_length"] == len(sample_transcript)

    @pytest.mark.asyncio
    async def test_generated_at_is_set(self, service, sample_transcript):
        report = await service.generate_report(
            interview_id=uuid4(),
            transcript=sample_transcript,
            report_type=ReportType.SUMMARY,
        )
        assert isinstance(report.generated_at, datetime)


# ---------------------------------------------------------------------------
# generate_report (AI provider path)
# ---------------------------------------------------------------------------


class TestGenerateReportWithAI:
    @pytest.mark.asyncio
    async def test_ai_provider_called(self, service_with_ai, mock_ai_provider, sample_transcript):
        mock_ai_provider.chat.return_value = MagicMock(
            content=json.dumps({"title": "AI生成レポート", "summary": "テスト要約"})
        )
        report = await service_with_ai.generate_report(
            interview_id=uuid4(),
            transcript=sample_transcript,
            report_type=ReportType.SUMMARY,
        )
        mock_ai_provider.chat.assert_awaited_once()
        assert report.title == "AI生成レポート"

    @pytest.mark.asyncio
    async def test_ai_invalid_json_fallback(
        self, service_with_ai, mock_ai_provider, sample_transcript
    ):
        mock_ai_provider.chat.return_value = MagicMock(content="not valid json {{{")
        report = await service_with_ai.generate_report(
            interview_id=uuid4(),
            transcript=sample_transcript,
            report_type=ReportType.SUMMARY,
        )
        assert "error" in report.content
        assert report.content["error"] == "JSON parse error"


# ---------------------------------------------------------------------------
# export_report - JSON
# ---------------------------------------------------------------------------


class TestExportJSON:
    @pytest.mark.asyncio
    async def test_export_json(self, service, sample_report):
        result = await service.export_report(sample_report, ExportFormat.JSON)
        assert isinstance(result, bytes)
        parsed = json.loads(result.decode("utf-8"))
        assert parsed["title"] == "インタビュー要約"

    @pytest.mark.asyncio
    async def test_export_json_utf8(self, service, sample_report):
        result = await service.export_report(sample_report, ExportFormat.JSON)
        text = result.decode("utf-8")
        assert "インタビュー" in text


# ---------------------------------------------------------------------------
# export_report - Markdown
# ---------------------------------------------------------------------------


class TestExportMarkdown:
    @pytest.mark.asyncio
    async def test_export_markdown_summary(self, service, sample_report):
        result = await service.export_report(sample_report, ExportFormat.MARKDOWN)
        text = result.decode("utf-8")
        assert text.startswith("# インタビュー要約")
        assert "## Summary" in text
        assert "## Key Findings" in text

    @pytest.mark.asyncio
    async def test_export_markdown_process_doc(self, service):
        report = GeneratedReport(
            report_type=ReportType.PROCESS_DOC,
            title="業務記述書",
            generated_at=datetime.utcnow(),
            content={
                "title": "業務記述書",
                "process_name": "月次決算",
                "process_owner": "経理部長",
                "objective": "正確な財務諸表作成",
                "narrative": "毎月の決算業務フロー。",
                "process_steps": [
                    {"step_number": 1, "description": "データ取得"},
                ],
            },
        )
        result = await service.export_report(report, ExportFormat.MARKDOWN)
        text = result.decode("utf-8")
        assert "## Process Overview" in text
        assert "月次決算" in text

    @pytest.mark.asyncio
    async def test_export_markdown_rcm(self, service):
        report = GeneratedReport(
            report_type=ReportType.RCM,
            title="RCM",
            generated_at=datetime.utcnow(),
            content={
                "title": "RCM",
                "items": [
                    {
                        "risk_id": "R001",
                        "risk_description": "売上計上の誤り",
                        "control_description": "照合チェック",
                        "residual_risk": "低",
                    }
                ],
            },
        )
        result = await service.export_report(report, ExportFormat.MARKDOWN)
        text = result.decode("utf-8")
        assert "Risk ID" in text
        assert "R001" in text

    @pytest.mark.asyncio
    async def test_export_markdown_audit(self, service):
        report = GeneratedReport(
            report_type=ReportType.AUDIT_WORKPAPER,
            title="監査調書",
            generated_at=datetime.utcnow(),
            content={
                "title": "監査調書",
                "objective": "有効性評価",
                "scope": "経理部門",
                "findings": [],
                "conclusion": "適切に運用されている",
            },
        )
        result = await service.export_report(report, ExportFormat.MARKDOWN)
        text = result.decode("utf-8")
        assert "## Conclusion" in text
        assert "適切に運用されている" in text


# ---------------------------------------------------------------------------
# export_report - Word (DOCX)
# ---------------------------------------------------------------------------


class TestExportWord:
    @pytest.mark.asyncio
    async def test_export_word_returns_bytes(self, service, sample_report):
        result = await service.export_report(sample_report, ExportFormat.WORD)
        assert isinstance(result, bytes)
        assert len(result) > 0
        # DOCX files start with PK (ZIP format)
        assert result[:2] == b"PK"

    @pytest.mark.asyncio
    async def test_export_word_rcm(self, service):
        report = GeneratedReport(
            report_type=ReportType.RCM,
            title="RCM",
            generated_at=datetime.utcnow(),
            content={
                "title": "RCM",
                "items": [
                    {
                        "risk_id": "R001",
                        "risk_description": "リスク",
                        "control_description": "統制",
                        "residual_risk": "低",
                    }
                ],
            },
        )
        result = await service.export_report(report, ExportFormat.WORD)
        assert result[:2] == b"PK"


# ---------------------------------------------------------------------------
# export_report - Excel (XLSX)
# ---------------------------------------------------------------------------


class TestExportExcel:
    @pytest.mark.asyncio
    async def test_export_excel_returns_bytes(self, service, sample_report):
        result = await service.export_report(sample_report, ExportFormat.EXCEL)
        assert isinstance(result, bytes)
        assert len(result) > 0
        assert result[:2] == b"PK"

    @pytest.mark.asyncio
    async def test_export_excel_rcm(self, service):
        report = GeneratedReport(
            report_type=ReportType.RCM,
            title="RCM",
            generated_at=datetime.utcnow(),
            content={
                "title": "RCM",
                "items": [
                    {
                        "risk_id": "R001",
                        "risk_description": "リスク",
                        "risk_category": "財務報告",
                        "likelihood": "中",
                        "impact": "高",
                        "control_id": "C001",
                        "control_description": "照合",
                        "control_type": "発見的",
                        "control_frequency": "月次",
                        "residual_risk": "低",
                    }
                ],
            },
        )
        result = await service.export_report(report, ExportFormat.EXCEL)
        assert result[:2] == b"PK"

    @pytest.mark.asyncio
    async def test_export_excel_process_doc(self, service):
        report = GeneratedReport(
            report_type=ReportType.PROCESS_DOC,
            title="業務記述書",
            generated_at=datetime.utcnow(),
            content={
                "title": "業務記述書",
                "process_steps": [
                    {
                        "step_number": 1,
                        "description": "データ取得",
                        "responsible_party": "経理",
                        "system_used": "SAP",
                    }
                ],
            },
        )
        result = await service.export_report(report, ExportFormat.EXCEL)
        assert result[:2] == b"PK"


# ---------------------------------------------------------------------------
# export_report - PDF
# ---------------------------------------------------------------------------


class TestExportPDF:
    @pytest.mark.asyncio
    async def test_export_pdf_returns_bytes(self, service, sample_report):
        result = await service.export_report(sample_report, ExportFormat.PDF)
        assert isinstance(result, bytes)
        assert len(result) > 0
        # PDF files start with %PDF
        assert result[:4] == b"%PDF"

    @pytest.mark.asyncio
    async def test_export_pdf_rcm(self, service):
        report = GeneratedReport(
            report_type=ReportType.RCM,
            title="RCM",
            generated_at=datetime.utcnow(),
            content={
                "title": "RCM",
                "items": [
                    {
                        "risk_id": "R001",
                        "risk_description": "リスク説明",
                        "control_description": "統制説明",
                        "residual_risk": "低",
                    }
                ],
            },
        )
        result = await service.export_report(report, ExportFormat.PDF)
        assert result[:4] == b"%PDF"


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_unsupported_export_format(self, service, sample_report):
        with pytest.raises(ValueError, match="Unsupported export format"):
            await service.export_report(sample_report, "invalid_format")
