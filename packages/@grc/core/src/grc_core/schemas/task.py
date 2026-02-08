"""Interview task schemas."""

from datetime import datetime
from typing import Any

from grc_core.enums import TaskStatus, UseCaseType
from grc_core.schemas.base import BaseSchema


class TaskBase(BaseSchema):
    """Base task schema."""

    name: str
    description: str | None = None
    use_case_type: UseCaseType
    target_count: int = 1
    deadline: datetime | None = None


class TaskCreate(TaskBase):
    """Schema for creating a task."""

    project_id: str
    template_id: str | None = None
    settings: dict[str, Any] = {}


class TaskUpdate(BaseSchema):
    """Schema for updating a task."""

    name: str | None = None
    description: str | None = None
    template_id: str | None = None
    target_count: int | None = None
    deadline: datetime | None = None
    status: TaskStatus | None = None
    settings: dict[str, Any] | None = None


class TaskRead(TaskBase):
    """Schema for reading a task."""

    id: str
    project_id: str
    template_id: str | None = None
    created_by: str | None = None
    status: TaskStatus
    settings: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    interview_count: int = 0
    completed_interview_count: int = 0
