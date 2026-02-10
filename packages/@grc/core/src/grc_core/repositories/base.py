"""Base repository with common CRUD operations."""

from typing import Any, Generic, TypeVar
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from grc_core.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository with common CRUD operations."""

    def __init__(self, session: AsyncSession, model: type[ModelType]) -> None:
        """Initialize repository.

        Args:
            session: SQLAlchemy async session
            model: SQLAlchemy model class
        """
        self.session = session
        self.model = model

    async def get(self, id: str) -> ModelType | None:
        """Get a single record by ID."""
        result = await self.session.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: dict[str, Any] | None = None,
    ) -> list[ModelType]:
        """Get multiple records with pagination and filtering."""
        query = select(self.model)

        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    query = query.where(getattr(self.model, key) == value)

        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(self, filters: dict[str, Any] | None = None) -> int:
        """Count records with optional filtering."""
        query = select(func.count(self.model.id))

        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    query = query.where(getattr(self.model, key) == value)

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def create(self, **data: Any) -> ModelType:
        """Create a new record."""
        if "id" not in data:
            data["id"] = str(uuid4())

        obj = self.model(**data)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, id: str, **data: Any) -> ModelType | None:
        """Update an existing record."""
        obj = await self.get(id)
        if obj is None:
            return None

        for key, value in data.items():
            if hasattr(obj, key) and value is not None:
                setattr(obj, key, value)

        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, id: str) -> bool:
        """Delete a record by ID."""
        obj = await self.get(id)
        if obj is None:
            return False

        await self.session.delete(obj)
        await self.session.flush()
        return True

    async def exists(self, id: str) -> bool:
        """Check if a record exists."""
        result = await self.session.execute(
            select(func.count(self.model.id)).where(self.model.id == id)
        )
        return (result.scalar() or 0) > 0
