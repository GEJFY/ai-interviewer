"""Template model for interview questions."""

from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from grc_core.enums import UseCaseType
from grc_core.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from grc_core.models.organization import Organization
    from grc_core.models.task import InterviewTask
    from grc_core.models.user import User


class Template(Base, TimestampMixin):
    """Template entity - stores interview question templates."""

    __tablename__ = "templates"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    use_case_type: Mapped[UseCaseType] = mapped_column(String(100), nullable=False)

    organization_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=True
    )
    created_by: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id"), nullable=True
    )

    # Questions structure: [{order, question, follow_ups, required, category}]
    questions: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    settings: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, server_default="{}")

    version: Mapped[int] = mapped_column(Integer, default=1)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    organization: Mapped["Organization | None"] = relationship(
        "Organization", back_populates="templates"
    )
    created_by_user: Mapped["User | None"] = relationship(
        "User", back_populates="created_templates", foreign_keys=[created_by]
    )
    tasks: Mapped[list["InterviewTask"]] = relationship("InterviewTask", back_populates="template")
