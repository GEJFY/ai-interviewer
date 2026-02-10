"""Interview management endpoints."""

from fastapi import APIRouter, HTTPException, Query, status

from grc_backend.api.deps import AIProviderDep, CurrentUser, DBSession
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
    current_user: CurrentUser,
) -> InterviewRead:
    """Create a new interview."""
    # Verify task exists
    task_repo = TaskRepository(db)
    task = await task_repo.get(interview_data.task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
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
    interview = await repo.get(interview_id)

    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found",
        )

    return InterviewRead.model_validate(interview)


@router.post("/{interview_id}/start", response_model=InterviewRead)
async def start_interview(
    interview_id: str,
    start_data: InterviewStart,
    db: DBSession,
    current_user: CurrentUser,
) -> InterviewRead:
    """Start an interview session."""
    repo = InterviewRepository(db)
    interview = await repo.get(interview_id)

    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found",
        )

    if interview.status not in (InterviewStatus.SCHEDULED, InterviewStatus.PAUSED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot start interview with status: {interview.status}",
        )

    interviewer_id = start_data.interviewer_id or current_user.id
    updated_interview = await repo.start(interview_id, interviewer_id)

    await db.commit()
    return InterviewRead.model_validate(updated_interview)


@router.post("/{interview_id}/pause", response_model=InterviewRead)
async def pause_interview(
    interview_id: str,
    db: DBSession,
    current_user: CurrentUser,
) -> InterviewRead:
    """Pause an interview session."""
    repo = InterviewRepository(db)
    interview = await repo.pause(interview_id)

    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found or cannot be paused",
        )

    await db.commit()
    return InterviewRead.model_validate(interview)


@router.post("/{interview_id}/resume", response_model=InterviewRead)
async def resume_interview(
    interview_id: str,
    db: DBSession,
    current_user: CurrentUser,
) -> InterviewRead:
    """Resume a paused interview session."""
    repo = InterviewRepository(db)
    interview = await repo.resume(interview_id)

    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found or cannot be resumed",
        )

    await db.commit()
    return InterviewRead.model_validate(interview)


@router.post("/{interview_id}/complete", response_model=InterviewRead)
async def complete_interview(
    interview_id: str,
    complete_data: InterviewComplete,
    db: DBSession,
    current_user: CurrentUser,
    ai_provider: AIProviderDep,
) -> InterviewRead:
    """Complete an interview session."""
    repo = InterviewRepository(db)
    interview = await repo.get(interview_id)

    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found",
        )

    # Complete the interview
    updated_interview = await repo.complete(
        interview_id,
        summary=complete_data.summary,
        ai_analysis=complete_data.ai_analysis,
    )

    # Update task status
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
    interview = await repo.get(interview_id)

    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found",
        )

    entries = await repo.get_transcript(interview_id)
    return [TranscriptEntryRead.model_validate(e) for e in entries]


@router.put("/{interview_id}", response_model=InterviewRead)
async def update_interview(
    interview_id: str,
    interview_data: InterviewUpdate,
    db: DBSession,
    current_user: CurrentUser,
) -> InterviewRead:
    """Update an interview."""
    repo = InterviewRepository(db)
    interview = await repo.get(interview_id)

    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found",
        )

    update_data = interview_data.model_dump(exclude_unset=True)
    updated_interview = await repo.update(interview_id, **update_data)

    await db.commit()
    return InterviewRead.model_validate(updated_interview)
