"""Project schemas."""

from datetime import date, datetime

from grc_core.enums import ProjectStatus
from grc_core.schemas.base import BaseSchema


class ProjectBase(BaseSchema):
    """Base project schema."""

    name: str
    description: str | None = None
    client_name: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class ProjectCreate(ProjectBase):
    """Schema for creating a project."""

    organization_id: str | None = None


class ProjectUpdate(BaseSchema):
    """Schema for updating a project."""

    name: str | None = None
    description: str | None = None
    client_name: str | None = None
    status: ProjectStatus | None = None
    start_date: date | None = None
    end_date: date | None = None


class ProjectRead(ProjectBase):
    """Schema for reading a project."""

    id: str
    organization_id: str | None = None
    created_by: str | None = None
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime
    task_count: int = 0
    completed_task_count: int = 0
