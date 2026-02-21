"""Interview task management endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from grc_backend.api.deps import AIProviderDep, CurrentUser, DBSession, ManagerUser
from grc_core.enums import InterviewStatus, TaskStatus
from grc_core.repositories import (
    InterviewRepository,
    ProjectRepository,
    TaskRepository,
    TemplateRepository,
)
from grc_core.schemas import TaskCreate, TaskRead, TaskUpdate
from grc_core.schemas.base import PaginatedResponse

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


@router.get("/{task_id}/compare")
async def compare_interviews(
    task_id: str,
    db: DBSession,
    current_user: CurrentUser,
    ai_provider: AIProviderDep,
) -> dict[str, Any]:
    """Compare answers across all completed interviews in a task.

    Returns per-question comparison with AI-generated analysis of
    common themes, discrepancies, and key insights.
    """
    from grc_ai.base import ChatMessage, MessageRole

    task_repo = TaskRepository(db)
    task = await task_repo.get(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    # Get all completed interviews for this task
    interview_repo = InterviewRepository(db)
    interviews = await interview_repo.get_by_task(task_id, status=InterviewStatus.COMPLETED)

    if len(interviews) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="比較には2件以上の完了済みインタビューが必要です",
        )

    # Get template questions
    questions: list[str] = []
    if task.template_id:
        template_repo = TemplateRepository(db)
        template = await template_repo.get(task.template_id)
        if template:
            questions = [q.get("question", "") for q in template.questions]

    # Gather transcripts
    interview_data = []
    for interview in interviews:
        entries = await interview_repo.get_transcript(interview.id)
        transcript = "\n".join(
            f"{'AI' if str(e.speaker) in ('ai', 'Speaker.AI') else '回答者'}: {e.content}"
            for e in entries
        )
        interview_data.append(
            {
                "id": interview.id,
                "summary": interview.summary or "",
                "transcript": transcript[:3000],  # Limit per interview
            }
        )

    # Build comparison prompt
    interviews_text = ""
    for i, data in enumerate(interview_data, 1):
        interviews_text += f"\n### インタビュー{i} (ID: {data['id'][:8]})\n{data['transcript']}\n"

    questions_text = (
        "\n".join(f"{i + 1}. {q}" for i, q in enumerate(questions))
        if questions
        else "質問リストなし"
    )

    prompt = f"""以下の{len(interview_data)}件のインタビューを横断的に比較分析してください。

## 質問リスト
{questions_text}

## インタビュー記録
{interviews_text}

## 出力形式（JSON）
{{
    "total_interviews": {len(interview_data)},
    "common_themes": ["共通テーマ1", "共通テーマ2"],
    "discrepancies": ["不一致点1", "不一致点2"],
    "per_question": [
        {{
            "question": "質問文",
            "responses_summary": "全回答の要約",
            "consensus": "一致度 (high/medium/low)",
            "notable_differences": "特筆すべき差異"
        }}
    ],
    "key_insights": ["洞察1", "洞察2"],
    "risk_flags": ["リスクフラグ1"]
}}
"""

    import json

    messages = [
        ChatMessage(
            role=MessageRole.SYSTEM,
            content="インタビュー横断分析の専門家として、JSONフォーマットで分析結果を出力してください。",
        ),
        ChatMessage(role=MessageRole.USER, content=prompt),
    ]

    response = await ai_provider.chat(messages, temperature=0.3, max_tokens=4096)

    try:
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        result = json.loads(content)
    except json.JSONDecodeError:
        result = {
            "total_interviews": len(interview_data),
            "common_themes": [],
            "discrepancies": [],
            "per_question": [],
            "key_insights": [response.content[:500]],
            "risk_flags": [],
        }

    return result
