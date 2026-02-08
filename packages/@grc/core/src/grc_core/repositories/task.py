"""Interview task repository."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from grc_core.enums import TaskStatus
from grc_core.models.task import InterviewTask
from grc_core.models.interview import Interview
from grc_core.repositories.base import BaseRepository


class TaskRepository(BaseRepository[InterviewTask]):
    """Repository for InterviewTask operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, InterviewTask)

    async def get_with_interviews(self, id: str) -> InterviewTask | None:
        """Get task with its interviews."""
        result = await self.session.execute(
            select(InterviewTask)
            .where(InterviewTask.id == id)
            .options(selectinload(InterviewTask.interviews))
        )
        return result.scalar_one_or_none()

    async def get_by_project(
        self,
        project_id: str,
        *,
        status: TaskStatus | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[InterviewTask]:
        """Get tasks by project."""
        query = select(InterviewTask).where(InterviewTask.project_id == project_id)

        if status:
            query = query.where(InterviewTask.status == status)

        query = query.offset(skip).limit(limit).order_by(InterviewTask.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_interview_counts(self, task_id: str) -> dict[str, int]:
        """Get interview counts for a task."""
        total = await self.session.execute(
            select(func.count(Interview.id)).where(Interview.task_id == task_id)
        )
        completed = await self.session.execute(
            select(func.count(Interview.id)).where(
                Interview.task_id == task_id,
                Interview.status == "completed",
            )
        )
        return {
            "total": total.scalar() or 0,
            "completed": completed.scalar() or 0,
        }

    async def update_status(self, task_id: str) -> InterviewTask | None:
        """Update task status based on interview completion."""
        task = await self.get_with_interviews(task_id)
        if task is None:
            return None

        total = len(task.interviews)
        completed = sum(1 for i in task.interviews if i.status == "completed")

        if total == 0:
            new_status = TaskStatus.PENDING
        elif completed >= task.target_count:
            new_status = TaskStatus.COMPLETED
        elif completed > 0:
            new_status = TaskStatus.IN_PROGRESS
        else:
            new_status = TaskStatus.PENDING

        task.status = new_status
        await self.session.flush()
        return task
