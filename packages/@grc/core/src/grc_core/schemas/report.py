"""Report schemas."""

from datetime import datetime
from typing import Any

from grc_core.enums import ReportStatus, ReportType
from grc_core.schemas.base import BaseSchema


class ReportBase(BaseSchema):
    """Base report schema."""

    report_type: ReportType
    title: str


class ReportCreate(ReportBase):
    """Schema for creating a report."""

    interview_id: str | None = None
    task_id: str | None = None
    content: dict[str, Any]
    format: str = "json"


class ReportGenerate(BaseSchema):
    """Schema for generating a report from interview(s)."""

    report_type: ReportType
    interview_id: str | None = None
    task_id: str | None = None
    template_id: str | None = None
    options: dict[str, Any] = {}


class ReportUpdate(BaseSchema):
    """Schema for updating a report."""

    title: str | None = None
    content: dict[str, Any] | None = None
    status: ReportStatus | None = None


class ReportRead(ReportBase):
    """Schema for reading a report."""

    id: str
    interview_id: str | None = None
    task_id: str | None = None
    created_by: str | None = None
    approved_by: str | None = None
    content: dict[str, Any]
    format: str
    status: ReportStatus
    approved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ReportExport(BaseSchema):
    """Schema for exporting a report."""

    format: str = "pdf"  # pdf, docx, xlsx, pptx
    include_metadata: bool = False
