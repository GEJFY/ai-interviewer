"""Transcript schemas."""

from datetime import datetime

from grc_core.enums import Speaker
from grc_core.schemas.base import BaseSchema


class TranscriptEntryBase(BaseSchema):
    """Base transcript entry schema."""

    speaker: Speaker
    content: str
    timestamp_ms: int
    duration_ms: int | None = None


class TranscriptEntryCreate(TranscriptEntryBase):
    """Schema for creating a transcript entry."""

    interview_id: str
    confidence: float | None = None
    content_translated: str | None = None


class TranscriptEntryUpdate(BaseSchema):
    """Schema for updating a transcript entry."""

    content: str
    content_translated: str | None = None


class TranscriptEntryRead(TranscriptEntryBase):
    """Schema for reading a transcript entry."""

    id: str
    interview_id: str
    content_translated: str | None = None
    confidence: float | None = None
    is_edited: bool
    original_content: str | None = None
    created_at: datetime
