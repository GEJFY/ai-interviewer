"""Organization model."""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from grc_core.models.base import Base

if TYPE_CHECKING:
    from grc_core.models.interviewee import Interviewee
    from grc_core.models.knowledge import KnowledgeItem
    from grc_core.models.project import Project
    from grc_core.models.template import Template
    from grc_core.models.user import User


class Organization(Base):
    """Organization entity - represents a client or company."""

    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    settings: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, server_default="{}"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    users: Mapped[list["User"]] = relationship(
        "User", back_populates="organization", lazy="selectin"
    )
    projects: Mapped[list["Project"]] = relationship(
        "Project", back_populates="organization", lazy="selectin"
    )
    templates: Mapped[list["Template"]] = relationship(
        "Template", back_populates="organization", lazy="selectin"
    )
    interviewees: Mapped[list["Interviewee"]] = relationship(
        "Interviewee", back_populates="organization", lazy="selectin"
    )
    knowledge_items: Mapped[list["KnowledgeItem"]] = relationship(
        "KnowledgeItem", back_populates="organization", lazy="selectin"
    )
