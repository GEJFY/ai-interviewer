"""Interview schemas."""

from datetime import datetime
from typing import Any

from grc_core.enums import InterviewStatus
from grc_core.schemas.base import BaseSchema


class InterviewBase(BaseSchema):
    """Base interview schema."""

    language: str = "ja"


class InterviewCreate(InterviewBase):
    """Schema for creating an interview."""

    task_id: str
    interviewee_id: str | None = None
    metadata: dict[str, Any] = {}


class InterviewUpdate(BaseSchema):
    """Schema for updating an interview."""

    language: str | None = None
    summary: str | None = None
    ai_analysis: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


class InterviewStart(BaseSchema):
    """Schema for starting an interview."""

    interviewer_id: str | None = None


class InterviewComplete(BaseSchema):
    """Schema for completing an interview."""

    summary: str | None = None
    ai_analysis: dict[str, Any] | None = None


class InterviewRead(InterviewBase):
    """Schema for reading an interview."""

    id: str
    task_id: str
    interviewee_id: str | None = None
    interviewer_id: str | None = None
    status: InterviewStatus
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_seconds: int | None = None
    summary: str | None = None
    ai_analysis: dict[str, Any] | None = None
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class InterviewWithTranscript(InterviewRead):
    """Interview with transcript entries."""

    transcript_count: int = 0
