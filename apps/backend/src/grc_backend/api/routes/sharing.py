"""Pre-interview question sharing endpoints.

Allows managers to generate a share link so interviewees can preview
the interview questions before the session starts.  The link uses a
short-lived JWT token — no extra database table is needed.
"""

from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError, jwt
from pydantic import BaseModel

from grc_backend.api.deps import DBSession, ManagerUser, get_settings_dep
from grc_backend.config import Settings
from grc_backend.core.errors import NotFoundError
from grc_core.repositories import InterviewRepository, TaskRepository, TemplateRepository

router = APIRouter()

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

SHARE_TOKEN_EXPIRE_DAYS = 7


class ShareLinkCreate(BaseModel):
    """Request to create a share link."""

    expires_days: int = SHARE_TOKEN_EXPIRE_DAYS


class ShareLinkResponse(BaseModel):
    """Response containing the generated share link."""

    token: str
    expires_at: datetime
    interview_id: str
    share_url: str


class SharedQuestions(BaseModel):
    """Public response with interview questions for preparation."""

    interview_id: str
    task_name: str
    template_name: str | None
    description: str | None
    questions: list[dict[str, Any]]
    estimated_duration_minutes: int | None
    language: str


# ---------------------------------------------------------------------------
# Authenticated endpoints (manager creates share link)
# ---------------------------------------------------------------------------


@router.post("/{interview_id}/share", response_model=ShareLinkResponse)
async def create_share_link(
    interview_id: str,
    db: DBSession,
    current_user: ManagerUser,
    settings: Annotated[Settings, Depends(get_settings_dep)],
    body: ShareLinkCreate | None = None,
) -> ShareLinkResponse:
    """Generate a share link for pre-interview question preview.

    The link contains a JWT token with the interview and task IDs.
    Only managers or admins can create share links.
    """
    expires_days = body.expires_days if body else SHARE_TOKEN_EXPIRE_DAYS

    interview_repo = InterviewRepository(db)
    interview = await interview_repo.get(interview_id)
    if not interview:
        raise NotFoundError(
            message="Interview not found",
            resource_type="Interview",
            resource_id=interview_id,
        )

    # Verify the task has a template with questions
    task_repo = TaskRepository(db)
    task = await task_repo.get(interview.task_id)
    if not task or not task.template_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="このインタビューにはテンプレートが設定されていません",
        )

    expires_at = datetime.now(UTC) + timedelta(days=expires_days)
    token = jwt.encode(
        {
            "sub": interview_id,
            "task_id": interview.task_id,
            "template_id": task.template_id,
            "type": "share",
            "exp": expires_at,
        },
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )

    return ShareLinkResponse(
        token=token,
        expires_at=expires_at,
        interview_id=interview_id,
        share_url=f"/share/{token}",
    )


# ---------------------------------------------------------------------------
# Public endpoint (no authentication required)
# ---------------------------------------------------------------------------


# Separate router for public access — mounted without auth middleware
public_router = APIRouter()


@public_router.get("/{token}", response_model=SharedQuestions)
async def get_shared_questions(
    token: str,
    db: DBSession,
    settings: Annotated[Settings, Depends(get_settings_dep)],
) -> SharedQuestions:
    """Retrieve interview questions via a share token.

    This endpoint does NOT require authentication — anyone with a valid
    (non-expired) share token can view the questions.
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        if payload.get("type") != "share":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="無効なトークンタイプです",
            )
    except JWTError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="共有リンクが無効または期限切れです",
        ) from err

    interview_id = payload["sub"]
    task_id = payload.get("task_id")
    template_id = payload.get("template_id")

    # Fetch task
    task_repo = TaskRepository(db)
    task = await task_repo.get(task_id) if task_id else None
    task_name = task.name if task else "不明なタスク"

    # Fetch template questions
    template_repo = TemplateRepository(db)
    template = await template_repo.get(template_id) if template_id else None

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="テンプレートが見つかりません",
        )

    # Fetch interview for language / duration
    interview_repo = InterviewRepository(db)
    interview = await interview_repo.get(interview_id)
    language = interview.language if interview else "ja"

    # Extract duration from task settings
    duration = None
    if task and task.settings:
        duration = task.settings.get("duration_minutes")

    return SharedQuestions(
        interview_id=interview_id,
        task_name=task_name,
        template_name=template.name,
        description=template.description,
        questions=template.questions,
        estimated_duration_minutes=duration,
        language=language,
    )
