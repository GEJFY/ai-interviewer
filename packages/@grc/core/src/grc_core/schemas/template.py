"""Template schemas."""

from datetime import datetime
from typing import Any

from grc_core.enums import UseCaseType
from grc_core.schemas.base import BaseSchema


class QuestionItem(BaseSchema):
    """Schema for a single question in a template."""

    order: int
    question: str
    follow_ups: list[str] = []
    required: bool = True
    category: str | None = None


class TemplateBase(BaseSchema):
    """Base template schema."""

    name: str
    description: str | None = None
    use_case_type: UseCaseType


class TemplateCreate(TemplateBase):
    """Schema for creating a template."""

    organization_id: str | None = None
    questions: list[QuestionItem] = []
    settings: dict[str, Any] = {}


class TemplateUpdate(BaseSchema):
    """Schema for updating a template."""

    name: str | None = None
    description: str | None = None
    questions: list[QuestionItem] | None = None
    settings: dict[str, Any] | None = None
    is_published: bool | None = None


class TemplateRead(TemplateBase):
    """Schema for reading a template."""

    id: str
    organization_id: str | None = None
    created_by: str | None = None
    questions: list[dict[str, Any]]
    settings: dict[str, Any]
    version: int
    is_published: bool
    created_at: datetime
    updated_at: datetime
