"""Template repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from grc_core.enums import UseCaseType
from grc_core.models.template import Template
from grc_core.repositories.base import BaseRepository


class TemplateRepository(BaseRepository[Template]):
    """Repository for Template operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Template)

    async def get_by_organization(
        self,
        organization_id: str,
        *,
        use_case_type: UseCaseType | None = None,
        published_only: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Template]:
        """Get templates by organization."""
        query = select(Template).where(Template.organization_id == organization_id)

        if use_case_type:
            query = query.where(Template.use_case_type == use_case_type)

        if published_only:
            query = query.where(Template.is_published == True)  # noqa: E712

        query = query.offset(skip).limit(limit).order_by(Template.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_published(
        self,
        *,
        use_case_type: UseCaseType | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Template]:
        """Get all published templates."""
        query = select(Template).where(Template.is_published == True)  # noqa: E712

        if use_case_type:
            query = query.where(Template.use_case_type == use_case_type)

        query = query.offset(skip).limit(limit).order_by(Template.name)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def clone(self, id: str, new_name: str | None = None) -> Template | None:
        """Clone a template."""
        original = await self.get(id)
        if original is None:
            return None

        clone_data = {
            "name": new_name or f"{original.name} (Copy)",
            "description": original.description,
            "use_case_type": original.use_case_type,
            "organization_id": original.organization_id,
            "questions": original.questions,
            "settings": original.settings,
            "is_published": False,
            "version": 1,
        }

        return await self.create(**clone_data)

    async def publish(self, id: str) -> Template | None:
        """Publish a template."""
        return await self.update(id, is_published=True)

    async def unpublish(self, id: str) -> Template | None:
        """Unpublish a template."""
        return await self.update(id, is_published=False)
