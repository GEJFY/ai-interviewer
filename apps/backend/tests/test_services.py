"""Unit tests for backend services."""

import pytest
from uuid import uuid4
from datetime import datetime

# Import services
from grc_backend.services.report_generator import (
    ReportGeneratorService,
    ReportType,
    ExportFormat,
)
from grc_backend.services.knowledge_service import (
    KnowledgeService,
)


class TestReportGeneratorService:
    """Tests for the report generator service."""

    @pytest.fixture
    def service(self):
        """Create a service instance without AI provider."""
        return ReportGeneratorService(ai_provider=None)

    @pytest.mark.asyncio
    async def test_generate_summary_report(self, service):
        """Test generating an interview summary report."""
        interview_id = uuid4()
        transcript = """
        インタビュアー: 月次決算プロセスについて教えてください。
        被インタビュー者: 毎月5営業日までに前月の財務諸表を作成しています。
        インタビュアー: 主な課題は何ですか？
        被インタビュー者: 手作業での照合作業が多く、時間がかかっています。
        """

        report = await service.generate_report(
            interview_id=interview_id,
            transcript=transcript,
            report_type=ReportType.SUMMARY,
        )

        assert report.report_type == ReportType.SUMMARY
        assert report.title is not None
        assert report.generated_at is not None
        assert report.content is not None
        assert "title" in report.content

    @pytest.mark.asyncio
    async def test_generate_process_doc(self, service):
        """Test generating a process document."""
        interview_id = uuid4()
        transcript = "業務プロセスに関するインタビュー内容"

        report = await service.generate_report(
            interview_id=interview_id,
            transcript=transcript,
            report_type=ReportType.PROCESS_DOC,
        )

        assert report.report_type == ReportType.PROCESS_DOC
        assert "process_name" in report.content
        assert "process_steps" in report.content

    @pytest.mark.asyncio
    async def test_generate_rcm(self, service):
        """Test generating an RCM report."""
        interview_id = uuid4()
        transcript = "リスクと統制に関するインタビュー内容"

        report = await service.generate_report(
            interview_id=interview_id,
            transcript=transcript,
            report_type=ReportType.RCM,
        )

        assert report.report_type == ReportType.RCM
        assert "items" in report.content
        assert "summary" in report.content

    @pytest.mark.asyncio
    async def test_generate_audit_workpaper(self, service):
        """Test generating an audit workpaper."""
        interview_id = uuid4()
        transcript = "監査手続きに関するインタビュー内容"

        report = await service.generate_report(
            interview_id=interview_id,
            transcript=transcript,
            report_type=ReportType.AUDIT_WORKPAPER,
        )

        assert report.report_type == ReportType.AUDIT_WORKPAPER
        assert "objective" in report.content
        assert "conclusion" in report.content

    @pytest.mark.asyncio
    async def test_export_to_json(self, service):
        """Test exporting report to JSON."""
        interview_id = uuid4()
        report = await service.generate_report(
            interview_id=interview_id,
            transcript="テスト内容",
            report_type=ReportType.SUMMARY,
        )

        exported = await service.export_report(report, ExportFormat.JSON)
        assert isinstance(exported, bytes)
        assert len(exported) > 0

    @pytest.mark.asyncio
    async def test_export_to_markdown(self, service):
        """Test exporting report to Markdown."""
        interview_id = uuid4()
        report = await service.generate_report(
            interview_id=interview_id,
            transcript="テスト内容",
            report_type=ReportType.SUMMARY,
        )

        exported = await service.export_report(report, ExportFormat.MARKDOWN)
        assert isinstance(exported, bytes)
        markdown = exported.decode("utf-8")
        assert "#" in markdown  # Should contain headers


class TestKnowledgeService:
    """Tests for the knowledge service."""

    @pytest.fixture
    def service(self):
        """Create a service instance without AI provider."""
        return KnowledgeService(ai_provider=None)

    @pytest.mark.asyncio
    async def test_add_knowledge(self, service):
        """Test adding knowledge to the store."""
        content = "月次決算プロセスでは、毎月5営業日までに財務諸表を作成します。"

        chunk_ids = await service.add_knowledge(
            content=content,
            source_id=uuid4(),
            source_type="interview",
        )

        assert len(chunk_ids) > 0

    @pytest.mark.asyncio
    async def test_search(self, service):
        """Test searching the knowledge base."""
        # Add some knowledge
        await service.add_knowledge(
            content="月次決算プロセスでは、毎月5営業日までに財務諸表を作成します。売上データの照合、費用計上、仕訳入力を行います。",
            source_id=uuid4(),
            source_type="interview",
        )

        # Search
        results = await service.search(
            query="財務諸表の作成",
            limit=5,
            min_score=0.0,  # Low threshold for mock embeddings
        )

        assert len(results) > 0
        assert results[0].score >= 0

    @pytest.mark.asyncio
    async def test_build_rag_context(self, service):
        """Test building RAG context."""
        # Add knowledge
        await service.add_knowledge(
            content="内部統制では、職務分離と承認プロセスが重要です。",
            source_id=uuid4(),
            source_type="document",
        )

        context = await service.build_rag_context(
            query="内部統制について",
            limit=3,
        )

        assert context.query == "内部統制について"
        assert context.combined_context is not None

    @pytest.mark.asyncio
    async def test_chunk_text(self, service):
        """Test text chunking."""
        long_text = "これは長いテキストです。" * 100

        chunks = service._chunk_text(long_text, chunk_size=200, overlap=50)

        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) <= 250  # Some flexibility due to sentence boundaries

    @pytest.mark.asyncio
    async def test_generate_embedding(self, service):
        """Test embedding generation."""
        embedding = await service.generate_embedding("テストテキスト")

        assert len(embedding) == service.vector_dimension
        assert all(isinstance(x, float) for x in embedding)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
