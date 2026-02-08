"""Knowledge item schemas."""

from datetime import datetime
from typing import Any

from pydantic import Field

from grc_core.schemas.base import BaseSchema


class KnowledgeItemCreate(BaseSchema):
    """Schema for creating a knowledge item."""

    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    source_type: str | None = Field(None, max_length=50)
    source_interview_id: str | None = None
    tags: list[str] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeItemRead(BaseSchema):
    """Schema for reading a knowledge item."""

    id: str
    organization_id: str | None = None
    source_interview_id: str | None = None
    title: str
    content: str
    source_type: str | None = None
    tags: list[str] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    # Optional: relevance score from search
    relevance_score: float | None = None


class KnowledgeSearchRequest(BaseSchema):
    """Schema for knowledge search request."""

    query: str = Field(..., min_length=1)
    limit: int = Field(20, ge=1, le=100)
    tags: list[str] | None = None
    source_type: str | None = None
