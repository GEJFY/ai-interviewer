"""Knowledge management endpoints."""

from fastapi import APIRouter, HTTPException, Query, status

from grc_backend.api.deps import AIProviderDep, CurrentUser, DBSession
from grc_core.models import KnowledgeItem
from grc_core.repositories.base import BaseRepository
from grc_core.schemas import (
    KnowledgeItemCreate,
    KnowledgeItemRead,
    KnowledgeSearchRequest,
)
from grc_core.schemas.base import PaginatedResponse

router = APIRouter()


class KnowledgeRepository(BaseRepository[KnowledgeItem]):
    """Knowledge item repository."""

    def __init__(self, session):
        super().__init__(session, KnowledgeItem)


@router.get("", response_model=PaginatedResponse[KnowledgeItemRead])
async def list_knowledge(
    db: DBSession,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    source_type: str | None = None,
    tags: str | None = None,
) -> PaginatedResponse[KnowledgeItemRead]:
    """List knowledge items."""
    repo = KnowledgeRepository(db)

    filters = {}
    if current_user.organization_id:
        filters["organization_id"] = current_user.organization_id
    if source_type:
        filters["source_type"] = source_type

    skip = (page - 1) * page_size
    items = await repo.get_multi(skip=skip, limit=page_size, filters=filters)
    total = await repo.count(filters=filters)

    return PaginatedResponse(
        items=[KnowledgeItemRead.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.post("/search")
async def search_knowledge(
    search_request: KnowledgeSearchRequest,
    db: DBSession,
    current_user: CurrentUser,
    ai_provider: AIProviderDep,
) -> dict:
    """Search knowledge items using semantic search."""
    from sqlalchemy import select

    KnowledgeRepository(db)

    # Generate embedding for the query
    query_embedding = await ai_provider.embed(search_request.query)

    # Build base query
    query = select(KnowledgeItem)

    # Filter by organization
    if current_user.organization_id:
        query = query.where(KnowledgeItem.organization_id == current_user.organization_id)

    # Filter by source_type if specified
    if search_request.source_type:
        query = query.where(KnowledgeItem.source_type == search_request.source_type)

    # Filter by tags if specified (any match)
    if search_request.tags:
        query = query.where(KnowledgeItem.tags.overlap(search_request.tags))

    # Execute query to get all matching items
    result = await db.execute(query)
    items = result.scalars().all()

    # Calculate similarity scores in Python
    # In production with pgvector, this would be done in SQL
    scored_items = []
    for item in items:
        if item.embedding:
            # Cosine similarity
            score = _cosine_similarity(query_embedding, item.embedding)
            scored_items.append((item, score))
        else:
            # Text-based fallback: simple keyword matching
            query_lower = search_request.query.lower()
            content_lower = item.content.lower()
            title_lower = item.title.lower()

            if query_lower in content_lower or query_lower in title_lower:
                # Assign a moderate score for keyword matches
                scored_items.append((item, 0.5))

    # Sort by score and limit
    scored_items.sort(key=lambda x: x[1], reverse=True)
    top_items = scored_items[: search_request.limit]

    # Convert to response
    response_items = []
    for item, score in top_items:
        item_dict = KnowledgeItemRead.model_validate(item).model_dump()
        item_dict["relevance_score"] = score
        response_items.append(item_dict)

    return {"items": response_items, "total": len(response_items)}


def _cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    import math

    if len(vec1) != len(vec2):
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec1, vec2, strict=False))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))

    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    return dot_product / (magnitude1 * magnitude2)


@router.get("/{knowledge_id}", response_model=KnowledgeItemRead)
async def get_knowledge(
    knowledge_id: str,
    db: DBSession,
    current_user: CurrentUser,
) -> KnowledgeItemRead:
    """Get a specific knowledge item."""
    repo = KnowledgeRepository(db)
    item = await repo.get(knowledge_id)

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge item not found",
        )

    return KnowledgeItemRead.model_validate(item)


@router.post("", response_model=KnowledgeItemRead, status_code=status.HTTP_201_CREATED)
async def create_knowledge(
    knowledge_data: KnowledgeItemCreate,
    db: DBSession,
    current_user: CurrentUser,
    ai_provider: AIProviderDep,
) -> KnowledgeItemRead:
    """Create a new knowledge item."""
    repo = KnowledgeRepository(db)

    # Generate embedding for the content
    embedding = await ai_provider.embed(knowledge_data.content)

    item = await repo.create(
        organization_id=current_user.organization_id,
        title=knowledge_data.title,
        content=knowledge_data.content,
        source_type=knowledge_data.source_type,
        source_interview_id=knowledge_data.source_interview_id,
        tags=knowledge_data.tags,
        embedding=embedding,
        metadata=knowledge_data.metadata,
    )

    await db.commit()
    return KnowledgeItemRead.model_validate(item)


@router.delete("/{knowledge_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge(
    knowledge_id: str,
    db: DBSession,
    current_user: CurrentUser,
) -> None:
    """Delete a knowledge item."""
    repo = KnowledgeRepository(db)

    if not await repo.exists(knowledge_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge item not found",
        )

    await repo.delete(knowledge_id)
    await db.commit()
