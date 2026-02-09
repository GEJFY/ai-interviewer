"""Interview task management endpoints."""

from fastapi import APIRouter, HTTPException, Query, status
from grc_core.enums import TaskStatus
from grc_core.repositories import ProjectRepository, TaskRepository
from grc_core.schemas import TaskCreate, TaskRead, TaskUpdate
from grc_core.schemas.base import PaginatedResponse

from grc_backend.api.deps import CurrentUser, DBSession, ManagerUser

router = APIRouter()


@router.get("", response_model=PaginatedResponse[TaskRead])
async def list_tasks(
    db: DBSession,
    current_user: CurrentUser,
    project_id: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: TaskStatus | None = None,
) -> PaginatedResponse[TaskRead]:
    """List all tasks, optionally filtered by project."""
    repo = TaskRepository(db)

    filters = {}
    if project_id:
        filters["project_id"] = project_id
    if status:
        filters["status"] = status

    skip = (page - 1) * page_size
    tasks = await repo.get_multi(skip=skip, limit=page_size, filters=filters)
    total = await repo.count(filters=filters)

    # Add interview counts
    items = []
    for task in tasks:
        counts = await repo.get_interview_counts(task.id)
        task_data = TaskRead.model_validate(task)
        task_data.interview_count = counts["total"]
        task_data.completed_interview_count = counts["completed"]
        items.append(task_data)

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    db: DBSession,
    current_user: ManagerUser,
) -> TaskRead:
    """Create a new interview task."""
    # Verify project exists and user has access
    project_repo = ProjectRepository(db)
    project = await project_repo.get(task_data.project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    if (
        current_user.organization_id
        and project.organization_id != current_user.organization_id
        and current_user.role != "admin"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    repo = TaskRepository(db)
    task = await repo.create(
        name=task_data.name,
        description=task_data.description,
        use_case_type=task_data.use_case_type,
        project_id=task_data.project_id,
        template_id=task_data.template_id,
        target_count=task_data.target_count,
        deadline=task_data.deadline,
        settings=task_data.settings,
        created_by=current_user.id,
    )

    await db.commit()
    return TaskRead.model_validate(task)


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(
    task_id: str,
    db: DBSession,
    current_user: CurrentUser,
) -> TaskRead:
    """Get a specific task."""
    repo = TaskRepository(db)
    task = await repo.get_with_interviews(task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    counts = await repo.get_interview_counts(task_id)
    result = TaskRead.model_validate(task)
    result.interview_count = counts["total"]
    result.completed_interview_count = counts["completed"]

    return result


@router.put("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: str,
    task_data: TaskUpdate,
    db: DBSession,
    current_user: ManagerUser,
) -> TaskRead:
    """Update a task."""
    repo = TaskRepository(db)
    task = await repo.get(task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    update_data = task_data.model_dump(exclude_unset=True)
    updated_task = await repo.update(task_id, **update_data)

    await db.commit()
    return TaskRead.model_validate(updated_task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    db: DBSession,
    current_user: ManagerUser,
) -> None:
    """Delete a task (cancel it)."""
    repo = TaskRepository(db)
    task = await repo.get(task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Cancel instead of hard delete
    await repo.update(task_id, status=TaskStatus.CANCELLED)
    await db.commit()
