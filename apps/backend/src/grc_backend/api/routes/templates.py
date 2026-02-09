"""Template management endpoints."""

from fastapi import APIRouter, HTTPException, Query, status
from grc_core.enums import UseCaseType
from grc_core.repositories import TemplateRepository
from grc_core.schemas import TemplateCreate, TemplateRead, TemplateUpdate
from grc_core.schemas.base import PaginatedResponse

from grc_backend.api.deps import CurrentUser, DBSession, ManagerUser

router = APIRouter()


@router.get("", response_model=PaginatedResponse[TemplateRead])
async def list_templates(
    db: DBSession,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    use_case_type: UseCaseType | None = None,
    published_only: bool = False,
) -> PaginatedResponse[TemplateRead]:
    """List all templates."""
    repo = TemplateRepository(db)

    if current_user.organization_id:
        templates = await repo.get_by_organization(
            current_user.organization_id,
            use_case_type=use_case_type,
            published_only=published_only,
            skip=(page - 1) * page_size,
            limit=page_size,
        )
        total = await repo.count(
            filters={
                "organization_id": current_user.organization_id,
                **({"use_case_type": use_case_type} if use_case_type else {}),
                **({"is_published": True} if published_only else {}),
            }
        )
    else:
        templates = await repo.get_published(
            use_case_type=use_case_type,
            skip=(page - 1) * page_size,
            limit=page_size,
        )
        total = len(templates)

    return PaginatedResponse(
        items=[TemplateRead.model_validate(t) for t in templates],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size if total > 0 else 0,
    )


@router.post("", response_model=TemplateRead, status_code=status.HTTP_201_CREATED)
async def create_template(
    template_data: TemplateCreate,
    db: DBSession,
    current_user: ManagerUser,
) -> TemplateRead:
    """Create a new template."""
    repo = TemplateRepository(db)

    template = await repo.create(
        name=template_data.name,
        description=template_data.description,
        use_case_type=template_data.use_case_type,
        organization_id=template_data.organization_id or current_user.organization_id,
        questions=[q.model_dump() for q in template_data.questions],
        settings=template_data.settings,
        created_by=current_user.id,
    )

    await db.commit()
    return TemplateRead.model_validate(template)


@router.get("/{template_id}", response_model=TemplateRead)
async def get_template(
    template_id: str,
    db: DBSession,
    current_user: CurrentUser,
) -> TemplateRead:
    """Get a specific template."""
    repo = TemplateRepository(db)
    template = await repo.get(template_id)

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )

    return TemplateRead.model_validate(template)


@router.put("/{template_id}", response_model=TemplateRead)
async def update_template(
    template_id: str,
    template_data: TemplateUpdate,
    db: DBSession,
    current_user: ManagerUser,
) -> TemplateRead:
    """Update a template."""
    repo = TemplateRepository(db)
    template = await repo.get(template_id)

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )

    update_data = template_data.model_dump(exclude_unset=True)
    if "questions" in update_data and update_data["questions"]:
        update_data["questions"] = [q.model_dump() if hasattr(q, 'model_dump') else q for q in update_data["questions"]]

    # Increment version
    update_data["version"] = template.version + 1

    updated_template = await repo.update(template_id, **update_data)

    await db.commit()
    return TemplateRead.model_validate(updated_template)


@router.post("/{template_id}/clone", response_model=TemplateRead)
async def clone_template(
    template_id: str,
    db: DBSession,
    current_user: ManagerUser,
    new_name: str | None = None,
) -> TemplateRead:
    """Clone a template."""
    repo = TemplateRepository(db)
    cloned = await repo.clone(template_id, new_name)

    if not cloned:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )

    # Update created_by
    cloned.created_by = current_user.id

    await db.commit()
    return TemplateRead.model_validate(cloned)


@router.post("/{template_id}/publish", response_model=TemplateRead)
async def publish_template(
    template_id: str,
    db: DBSession,
    current_user: ManagerUser,
) -> TemplateRead:
    """Publish a template."""
    repo = TemplateRepository(db)
    template = await repo.publish(template_id)

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )

    await db.commit()
    return TemplateRead.model_validate(template)


@router.post("/{template_id}/unpublish", response_model=TemplateRead)
async def unpublish_template(
    template_id: str,
    db: DBSession,
    current_user: ManagerUser,
) -> TemplateRead:
    """Unpublish a template."""
    repo = TemplateRepository(db)
    template = await repo.unpublish(template_id)

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )

    await db.commit()
    return TemplateRead.model_validate(template)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: str,
    db: DBSession,
    current_user: ManagerUser,
) -> None:
    """Delete a template."""
    repo = TemplateRepository(db)

    if not await repo.exists(template_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )

    await repo.delete(template_id)
    await db.commit()
