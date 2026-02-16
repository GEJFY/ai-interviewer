"""Interview management endpoints."""

from fastapi import APIRouter, Query, status

from grc_backend.api.deps import AIProviderDep, CurrentUser, DBSession, InterviewerUser
from grc_backend.core.errors import NotFoundError, ValidationError
from grc_core.enums import InterviewStatus
from grc_core.repositories import InterviewRepository, TaskRepository
from grc_core.schemas import (
    InterviewComplete,
    InterviewCreate,
    InterviewRead,
    InterviewStart,
    InterviewUpdate,
)
from grc_core.schemas.base import PaginatedResponse
from grc_core.schemas.transcript import TranscriptEntryRead

router = APIRouter()

# ステートマシン: 各操作で許可される現在ステータス
_ALLOWED_TRANSITIONS: dict[str, set[InterviewStatus]] = {
    "start": {InterviewStatus.SCHEDULED, InterviewStatus.PAUSED},
    "pause": {InterviewStatus.IN_PROGRESS},
    "resume": {InterviewStatus.PAUSED},
    "complete": {InterviewStatus.IN_PROGRESS, InterviewStatus.PAUSED},
}


def _validate_transition(interview, action: str) -> None:
    """インタビューのステータス遷移を検証する。"""
    allowed = _ALLOWED_TRANSITIONS.get(action, set())
    if interview.status not in allowed:
        raise ValidationError(
            message=f"Cannot {action} interview with status: {interview.status.value}",
        )


async def _get_interview_or_raise(repo: InterviewRepository, interview_id: str):
    """インタビューを取得し、なければ NotFoundError を送出する。"""
    interview = await repo.get(interview_id)
    if not interview:
        raise NotFoundError(
            message="Interview not found",
            resource_type="Interview",
            resource_id=interview_id,
        )
    return interview


@router.get("", response_model=PaginatedResponse[InterviewRead])
async def list_interviews(
    db: DBSession,
    current_user: CurrentUser,
    task_id: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: InterviewStatus | None = None,
) -> PaginatedResponse[InterviewRead]:
    """List all interviews, optionally filtered by task."""
    repo = InterviewRepository(db)

    filters = {}
    if task_id:
        filters["task_id"] = task_id
    if status:
        filters["status"] = status

    skip = (page - 1) * page_size
    interviews = await repo.get_multi(skip=skip, limit=page_size, filters=filters)
    total = await repo.count(filters=filters)

    return PaginatedResponse(
        items=[InterviewRead.model_validate(i) for i in interviews],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.post("", response_model=InterviewRead, status_code=status.HTTP_201_CREATED)
async def create_interview(
    interview_data: InterviewCreate,
    db: DBSession,
    current_user: InterviewerUser,
) -> InterviewRead:
    """Create a new interview."""
    task_repo = TaskRepository(db)
    task = await task_repo.get(interview_data.task_id)

    if not task:
        raise NotFoundError(
            message="Task not found",
            resource_type="Task",
            resource_id=interview_data.task_id,
        )

    repo = InterviewRepository(db)
    interview = await repo.create(
        task_id=interview_data.task_id,
        interviewee_id=interview_data.interviewee_id,
        language=interview_data.language,
        metadata=interview_data.metadata,
    )

    await db.commit()
    return InterviewRead.model_validate(interview)


@router.get("/{interview_id}", response_model=InterviewRead)
async def get_interview(
    interview_id: str,
    db: DBSession,
    current_user: CurrentUser,
) -> InterviewRead:
    """Get a specific interview."""
    repo = InterviewRepository(db)
    interview = await _get_interview_or_raise(repo, interview_id)
    return InterviewRead.model_validate(interview)


@router.post("/{interview_id}/start", response_model=InterviewRead)
async def start_interview(
    interview_id: str,
    start_data: InterviewStart,
    db: DBSession,
    current_user: InterviewerUser,
) -> InterviewRead:
    """Start an interview session."""
    repo = InterviewRepository(db)
    interview = await _get_interview_or_raise(repo, interview_id)
    _validate_transition(interview, "start")

    interviewer_id = start_data.interviewer_id or current_user.id
    updated_interview = await repo.start(interview_id, interviewer_id)

    await db.commit()
    return InterviewRead.model_validate(updated_interview)


@router.post("/{interview_id}/pause", response_model=InterviewRead)
async def pause_interview(
    interview_id: str,
    db: DBSession,
    current_user: InterviewerUser,
) -> InterviewRead:
    """Pause an interview session."""
    repo = InterviewRepository(db)
    interview = await _get_interview_or_raise(repo, interview_id)
    _validate_transition(interview, "pause")

    updated = await repo.pause(interview_id)
    await db.commit()
    return InterviewRead.model_validate(updated)


@router.post("/{interview_id}/resume", response_model=InterviewRead)
async def resume_interview(
    interview_id: str,
    db: DBSession,
    current_user: InterviewerUser,
) -> InterviewRead:
    """Resume a paused interview session."""
    repo = InterviewRepository(db)
    interview = await _get_interview_or_raise(repo, interview_id)
    _validate_transition(interview, "resume")

    updated = await repo.resume(interview_id)
    await db.commit()
    return InterviewRead.model_validate(updated)


@router.post("/{interview_id}/complete", response_model=InterviewRead)
async def complete_interview(
    interview_id: str,
    complete_data: InterviewComplete,
    db: DBSession,
    current_user: InterviewerUser,
    ai_provider: AIProviderDep,
) -> InterviewRead:
    """Complete an interview session."""
    repo = InterviewRepository(db)
    interview = await _get_interview_or_raise(repo, interview_id)
    _validate_transition(interview, "complete")

    updated_interview = await repo.complete(
        interview_id,
        summary=complete_data.summary,
        ai_analysis=complete_data.ai_analysis,
    )

    task_repo = TaskRepository(db)
    await task_repo.update_status(interview.task_id)

    await db.commit()
    return InterviewRead.model_validate(updated_interview)


@router.get("/{interview_id}/transcript", response_model=list[TranscriptEntryRead])
async def get_transcript(
    interview_id: str,
    db: DBSession,
    current_user: CurrentUser,
) -> list[TranscriptEntryRead]:
    """Get the transcript of an interview."""
    repo = InterviewRepository(db)
    await _get_interview_or_raise(repo, interview_id)

    entries = await repo.get_transcript(interview_id)
    return [TranscriptEntryRead.model_validate(e) for e in entries]


@router.put("/{interview_id}", response_model=InterviewRead)
async def update_interview(
    interview_id: str,
    interview_data: InterviewUpdate,
    db: DBSession,
    current_user: InterviewerUser,
) -> InterviewRead:
    """Update an interview."""
    repo = InterviewRepository(db)
    await _get_interview_or_raise(repo, interview_id)

    update_data = interview_data.model_dump(exclude_unset=True)
    updated_interview = await repo.update(interview_id, **update_data)

    await db.commit()
    return InterviewRead.model_validate(updated_interview)
