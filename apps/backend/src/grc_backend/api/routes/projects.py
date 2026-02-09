"""Project management endpoints."""

from fastapi import APIRouter, HTTPException, Query, status

from grc_backend.api.deps import CurrentUser, DBSession, ManagerUser
from grc_core.enums import ProjectStatus
from grc_core.repositories import ProjectRepository
from grc_core.schemas import ProjectCreate, ProjectRead, ProjectUpdate
from grc_core.schemas.base import PaginatedResponse

router = APIRouter()


@router.get("", response_model=PaginatedResponse[ProjectRead])
async def list_projects(
    db: DBSession,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: ProjectStatus | None = None,
) -> PaginatedResponse[ProjectRead]:
    """List all projects accessible to the user."""
    repo = ProjectRepository(db)

    filters = {}
    if current_user.organization_id:
        filters["organization_id"] = current_user.organization_id
    if status:
        filters["status"] = status

    skip = (page - 1) * page_size
    projects = await repo.get_multi(skip=skip, limit=page_size, filters=filters)
    total = await repo.count(filters=filters)

    # Add task counts
    items = []
    for project in projects:
        counts = await repo.get_task_counts(project.id)
        project_data = ProjectRead.model_validate(project)
        project_data.task_count = counts["total"]
        project_data.completed_task_count = counts["completed"]
        items.append(project_data)

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    db: DBSession,
    current_user: ManagerUser,
) -> ProjectRead:
    """Create a new project."""
    repo = ProjectRepository(db)

    project = await repo.create(
        name=project_data.name,
        description=project_data.description,
        client_name=project_data.client_name,
        start_date=project_data.start_date,
        end_date=project_data.end_date,
        organization_id=project_data.organization_id or current_user.organization_id,
        created_by=current_user.id,
    )

    await db.commit()
    return ProjectRead.model_validate(project)


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: str,
    db: DBSession,
    current_user: CurrentUser,
) -> ProjectRead:
    """Get a specific project."""
    repo = ProjectRepository(db)
    project = await repo.get_with_tasks(project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Check access
    if (
        current_user.organization_id
        and project.organization_id != current_user.organization_id
        and current_user.role != "admin"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    counts = await repo.get_task_counts(project_id)
    result = ProjectRead.model_validate(project)
    result.task_count = counts["total"]
    result.completed_task_count = counts["completed"]

    return result


@router.put("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    db: DBSession,
    current_user: ManagerUser,
) -> ProjectRead:
    """Update a project."""
    repo = ProjectRepository(db)
    project = await repo.get(project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Check access
    if (
        current_user.organization_id
        and project.organization_id != current_user.organization_id
        and current_user.role != "admin"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    update_data = project_data.model_dump(exclude_unset=True)
    updated_project = await repo.update(project_id, **update_data)

    await db.commit()
    return ProjectRead.model_validate(updated_project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    db: DBSession,
    current_user: ManagerUser,
) -> None:
    """Delete a project (soft delete by archiving)."""
    repo = ProjectRepository(db)
    project = await repo.get(project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Check access
    if (
        current_user.organization_id
        and project.organization_id != current_user.organization_id
        and current_user.role != "admin"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # Soft delete by archiving
    await repo.update(project_id, status=ProjectStatus.ARCHIVED)
    await db.commit()
