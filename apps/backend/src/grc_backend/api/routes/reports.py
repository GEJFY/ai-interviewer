"""Report management endpoints."""

import io
import json
from datetime import UTC
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from grc_core.enums import ReportStatus, ReportType
from grc_core.models import Report
from grc_core.repositories import InterviewRepository
from grc_core.repositories.base import BaseRepository
from grc_core.schemas import ReportGenerate, ReportRead
from grc_core.schemas.base import PaginatedResponse
from pydantic import BaseModel

from grc_backend.api.deps import AIProviderDep, CurrentUser, DBSession

router = APIRouter()


class ReportRepository(BaseRepository[Report]):
    """Report repository."""

    def __init__(self, session):
        super().__init__(session, Report)


@router.get("", response_model=PaginatedResponse[ReportRead])
async def list_reports(
    db: DBSession,
    current_user: CurrentUser,
    interview_id: str | None = None,
    task_id: str | None = None,
    report_type: ReportType | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[ReportRead]:
    """List all reports."""
    repo = ReportRepository(db)

    filters = {}
    if interview_id:
        filters["interview_id"] = interview_id
    if task_id:
        filters["task_id"] = task_id
    if report_type:
        filters["report_type"] = report_type

    skip = (page - 1) * page_size
    reports = await repo.get_multi(skip=skip, limit=page_size, filters=filters)
    total = await repo.count(filters=filters)

    return PaginatedResponse(
        items=[ReportRead.model_validate(r) for r in reports],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.post("/generate", response_model=ReportRead, status_code=status.HTTP_201_CREATED)
async def generate_report(
    report_data: ReportGenerate,
    db: DBSession,
    current_user: CurrentUser,
    ai_provider: AIProviderDep,
) -> ReportRead:
    """Generate a report from interview(s) using AI."""
    interview_repo = InterviewRepository(db)

    if report_data.interview_id:
        # Generate report for single interview
        interview = await interview_repo.get_with_transcript(report_data.interview_id)
        if not interview:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview not found",
            )

        # Build transcript text
        transcript_text = "\n".join(
            f"{'AI' if e.speaker == 'ai' else '回答者'}: {e.content}"
            for e in interview.transcript_entries
        )

        # Generate based on report type
        content = await _generate_report_content(
            ai_provider,
            report_data.report_type,
            transcript_text,
            report_data.options,
        )

        title = f"{report_data.report_type.value} - Interview {interview.id[:8]}"

    elif report_data.task_id:
        # Generate aggregated report for task
        interviews = await interview_repo.get_by_task(report_data.task_id, status="completed")

        if not interviews:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No completed interviews found for task",
            )

        # Aggregate transcript
        all_transcripts = []
        for interview in interviews:
            full_interview = await interview_repo.get_with_transcript(interview.id)
            if full_interview:
                transcript = "\n".join(
                    f"{'AI' if e.speaker == 'ai' else '回答者'}: {e.content}"
                    for e in full_interview.transcript_entries
                )
                all_transcripts.append(f"--- Interview {interview.id[:8]} ---\n{transcript}")

        combined_transcript = "\n\n".join(all_transcripts)

        content = await _generate_report_content(
            ai_provider,
            report_data.report_type,
            combined_transcript,
            report_data.options,
        )

        title = f"{report_data.report_type.value} - Task Aggregate"

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either interview_id or task_id is required",
        )

    # Save report
    report_repo = ReportRepository(db)
    report = await report_repo.create(
        interview_id=report_data.interview_id,
        task_id=report_data.task_id,
        report_type=report_data.report_type,
        title=title,
        content=content,
        created_by=current_user.id,
    )

    await db.commit()
    return ReportRead.model_validate(report)


async def _generate_report_content(
    ai_provider,
    report_type: ReportType,
    transcript: str,
    options: dict[str, Any],
) -> dict[str, Any]:
    """Generate report content using AI."""
    from grc_ai.base import ChatMessage, MessageRole

    prompts = {
        ReportType.SUMMARY: """以下のインタビュー記録を要約してください。

{transcript}

以下のJSON形式で出力してください：
{{
    "summary": "概要（300文字以内）",
    "key_findings": ["発見事項1", "発見事項2", ...],
    "recommendations": ["提言1", "提言2", ...],
    "follow_up_items": ["フォローアップ項目1", ...]
}}""",
        ReportType.PROCESS_DOC: """以下のインタビュー記録から業務プロセス記述書を作成してください。

{transcript}

以下のJSON形式で出力してください：
{{
    "process_name": "業務プロセス名",
    "purpose": "目的",
    "scope": "対象範囲",
    "steps": [
        {{"order": 1, "activity": "活動内容", "responsible": "担当者", "input": "入力", "output": "出力"}},
        ...
    ],
    "controls": ["統制1", "統制2", ...],
    "risks": ["リスク1", "リスク2", ...]
}}""",
        ReportType.RCM: """以下のインタビュー記録からリスクコントロールマトリクス(RCM)を作成してください。

{transcript}

以下のJSON形式で出力してください：
{{
    "process_name": "業務プロセス名",
    "risks": [
        {{
            "id": "R1",
            "description": "リスク内容",
            "likelihood": "高/中/低",
            "impact": "高/中/低",
            "controls": [
                {{"id": "C1", "description": "統制内容", "type": "予防/発見", "frequency": "日次/週次/月次"}}
            ]
        }}
    ]
}}""",
        ReportType.AUDIT_WORKPAPER: """以下のインタビュー記録から監査調書を作成してください。

{transcript}

以下のJSON形式で出力してください：
{{
    "audit_objective": "監査目的",
    "scope": "監査範囲",
    "procedures_performed": ["実施した手続1", "手続2", ...],
    "findings": [
        {{"finding": "発見事項", "risk_level": "高/中/低", "recommendation": "改善提言", "management_response": ""}}
    ],
    "conclusion": "結論"
}}""",
        ReportType.SURVEY_ANALYSIS: """以下のインタビュー記録から意識調査分析レポートを作成してください。

{transcript}

以下のJSON形式で出力してください：
{{
    "survey_topic": "調査テーマ",
    "response_summary": "回答概要",
    "key_themes": ["主要テーマ1", "テーマ2", ...],
    "sentiment_analysis": {{"positive": 0.0, "neutral": 0.0, "negative": 0.0}},
    "recommendations": ["提言1", "提言2", ...],
    "areas_for_improvement": ["改善点1", "改善点2", ...]
}}""",
    }

    prompt = prompts.get(report_type, prompts[ReportType.SUMMARY]).format(
        transcript=transcript
    )

    messages = [
        ChatMessage(role=MessageRole.SYSTEM, content="JSONフォーマットで出力してください。説明は不要です。"),
        ChatMessage(role=MessageRole.USER, content=prompt),
    ]

    response = await ai_provider.chat(messages, temperature=0.3, max_tokens=4096)

    try:
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        return json.loads(content)
    except json.JSONDecodeError:
        return {"raw_content": response.content}


@router.get("/{report_id}", response_model=ReportRead)
async def get_report(
    report_id: str,
    db: DBSession,
    current_user: CurrentUser,
) -> ReportRead:
    """Get a specific report."""
    repo = ReportRepository(db)
    report = await repo.get(report_id)

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    return ReportRead.model_validate(report)


class ReportUpdateRequest(BaseModel):
    """Request model for updating report content."""
    content: dict[str, Any] | None = None
    title: str | None = None


@router.put("/{report_id}", response_model=ReportRead)
async def update_report(
    report_id: str,
    update_data: ReportUpdateRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> ReportRead:
    """Update a report's content."""
    repo = ReportRepository(db)
    report = await repo.get(report_id)

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    if report.status not in [ReportStatus.DRAFT, ReportStatus.REVIEW]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot edit approved or published reports",
        )

    update_fields = {}
    if update_data.content is not None:
        update_fields["content"] = update_data.content
    if update_data.title is not None:
        update_fields["title"] = update_data.title

    if update_fields:
        report = await repo.update(report_id, **update_fields)
        await db.commit()

    return ReportRead.model_validate(report)


@router.post("/{report_id}/submit-review", response_model=ReportRead)
async def submit_report_for_review(
    report_id: str,
    db: DBSession,
    current_user: CurrentUser,
) -> ReportRead:
    """Submit a report for review."""
    repo = ReportRepository(db)
    report = await repo.get(report_id)

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    if report.status != ReportStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only draft reports can be submitted for review",
        )

    report = await repo.update(report_id, status=ReportStatus.REVIEW)
    await db.commit()

    return ReportRead.model_validate(report)


@router.get("/{report_id}/export")
async def export_report(
    report_id: str,
    db: DBSession,
    current_user: CurrentUser,
    format: str = Query("json", pattern="^(json|pdf|docx)$"),
) -> StreamingResponse:
    """Export a report in various formats."""
    repo = ReportRepository(db)
    report = await repo.get(report_id)

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    if format == "json":
        content = json.dumps(report.content, ensure_ascii=False, indent=2)
        return StreamingResponse(
            io.BytesIO(content.encode("utf-8")),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=report_{report_id}.json"},
        )
    else:
        # PDF/DOCX export would require additional libraries
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"Export to {format} is not yet implemented",
        )


@router.post("/{report_id}/approve", response_model=ReportRead)
async def approve_report(
    report_id: str,
    db: DBSession,
    current_user: CurrentUser,
) -> ReportRead:
    """Approve a report."""
    from datetime import datetime

    repo = ReportRepository(db)
    report = await repo.get(report_id)

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    if report.status != ReportStatus.REVIEW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only reports under review can be approved",
        )

    report = await repo.update(
        report_id,
        status=ReportStatus.APPROVED,
        approved_by=current_user.id,
        approved_at=datetime.now(UTC),
    )

    await db.commit()
    return ReportRead.model_validate(report)
