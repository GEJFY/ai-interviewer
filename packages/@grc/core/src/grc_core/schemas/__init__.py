"""Pydantic schemas for API request/response validation."""

from grc_core.schemas.base import BaseSchema, PaginatedResponse
from grc_core.schemas.interview import (
    InterviewComplete,
    InterviewCreate,
    InterviewRead,
    InterviewStart,
    InterviewUpdate,
)
from grc_core.schemas.knowledge import (
    KnowledgeItemCreate,
    KnowledgeItemRead,
    KnowledgeSearchRequest,
)
from grc_core.schemas.notification import NotificationCreate, NotificationRead, UnreadCountResponse
from grc_core.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from grc_core.schemas.report import ReportCreate, ReportGenerate, ReportRead
from grc_core.schemas.task import TaskCreate, TaskRead, TaskUpdate
from grc_core.schemas.template import TemplateCreate, TemplateRead, TemplateUpdate
from grc_core.schemas.transcript import TranscriptEntryCreate, TranscriptEntryRead
from grc_core.schemas.user import UserCreate, UserRead, UserUpdate

__all__ = [
    "BaseSchema",
    "PaginatedResponse",
    "UserCreate",
    "UserRead",
    "UserUpdate",
    "ProjectCreate",
    "ProjectRead",
    "ProjectUpdate",
    "TaskCreate",
    "TaskRead",
    "TaskUpdate",
    "InterviewCreate",
    "InterviewRead",
    "InterviewUpdate",
    "InterviewStart",
    "InterviewComplete",
    "TemplateCreate",
    "TemplateRead",
    "TemplateUpdate",
    "TranscriptEntryCreate",
    "TranscriptEntryRead",
    "ReportCreate",
    "ReportRead",
    "ReportGenerate",
    "KnowledgeItemCreate",
    "KnowledgeItemRead",
    "KnowledgeSearchRequest",
    "NotificationCreate",
    "NotificationRead",
    "UnreadCountResponse",
]
