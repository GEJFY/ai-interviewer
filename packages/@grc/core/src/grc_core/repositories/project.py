"""Project repository."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from grc_core.enums import ProjectStatus
from grc_core.models.project import Project
from grc_core.models.task import InterviewTask
from grc_core.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    """Repository for Project operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Project)

    async def get_with_tasks(self, id: str) -> Project | None:
        """Get project with its tasks."""
        result = await self.session.execute(
            select(Project).where(Project.id == id).options(selectinload(Project.tasks))
        )
        return result.scalar_one_or_none()

    async def get_by_organization(
        self,
        organization_id: str,
        *,
        status: ProjectStatus | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Project]:
        """Get projects by organization."""
        query = select(Project).where(Project.organization_id == organization_id)

        if status:
            query = query.where(Project.status == status)

        query = query.offset(skip).limit(limit).order_by(Project.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_task_counts(self, project_id: str) -> dict[str, int]:
        """Get task counts for a project."""
        total = await self.session.execute(
            select(func.count(InterviewTask.id)).where(InterviewTask.project_id == project_id)
        )
        completed = await self.session.execute(
            select(func.count(InterviewTask.id)).where(
                InterviewTask.project_id == project_id,
                InterviewTask.status == "completed",
            )
        )
        return {
            "total": total.scalar() or 0,
            "completed": completed.scalar() or 0,
        }
