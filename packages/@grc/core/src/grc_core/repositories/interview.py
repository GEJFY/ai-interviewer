"""Interview repository."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from grc_core.enums import InterviewStatus
from grc_core.models.interview import Interview
from grc_core.models.transcript import TranscriptEntry
from grc_core.repositories.base import BaseRepository


class InterviewRepository(BaseRepository[Interview]):
    """Repository for Interview operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Interview)

    async def get_with_transcript(self, id: str) -> Interview | None:
        """Get interview with its transcript entries."""
        result = await self.session.execute(
            select(Interview)
            .where(Interview.id == id)
            .options(selectinload(Interview.transcript_entries))
        )
        return result.scalar_one_or_none()

    async def get_by_task(
        self,
        task_id: str,
        *,
        status: InterviewStatus | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Interview]:
        """Get interviews by task."""
        query = select(Interview).where(Interview.task_id == task_id)

        if status:
            query = query.where(Interview.status == status)

        query = query.offset(skip).limit(limit).order_by(Interview.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def start(self, id: str, interviewer_id: str | None = None) -> Interview | None:
        """Start an interview session."""
        interview = await self.get(id)
        if interview is None:
            return None

        interview.status = InterviewStatus.IN_PROGRESS
        interview.started_at = datetime.utcnow()
        if interviewer_id:
            interview.interviewer_id = interviewer_id

        await self.session.flush()
        return interview

    async def pause(self, id: str) -> Interview | None:
        """Pause an interview session."""
        interview = await self.get(id)
        if interview is None or interview.status != InterviewStatus.IN_PROGRESS:
            return None

        interview.status = InterviewStatus.PAUSED
        await self.session.flush()
        return interview

    async def resume(self, id: str) -> Interview | None:
        """Resume a paused interview session."""
        interview = await self.get(id)
        if interview is None or interview.status != InterviewStatus.PAUSED:
            return None

        interview.status = InterviewStatus.IN_PROGRESS
        await self.session.flush()
        return interview

    async def complete(
        self,
        id: str,
        summary: str | None = None,
        ai_analysis: dict | None = None,
    ) -> Interview | None:
        """Complete an interview session."""
        interview = await self.get(id)
        if interview is None:
            return None

        interview.status = InterviewStatus.COMPLETED
        interview.completed_at = datetime.utcnow()

        if interview.started_at:
            delta = interview.completed_at - interview.started_at
            interview.duration_seconds = int(delta.total_seconds())

        if summary:
            interview.summary = summary
        if ai_analysis:
            interview.ai_analysis = ai_analysis

        await self.session.flush()
        return interview

    async def add_transcript_entry(
        self,
        interview_id: str,
        speaker: str,
        content: str,
        timestamp_ms: int,
        **kwargs,
    ) -> TranscriptEntry:
        """Add a transcript entry to an interview."""
        entry = TranscriptEntry(
            interview_id=interview_id,
            speaker=speaker,
            content=content,
            timestamp_ms=timestamp_ms,
            **kwargs,
        )
        self.session.add(entry)
        await self.session.flush()
        return entry

    async def get_transcript(self, interview_id: str) -> list[TranscriptEntry]:
        """Get transcript entries for an interview."""
        result = await self.session.execute(
            select(TranscriptEntry)
            .where(TranscriptEntry.interview_id == interview_id)
            .order_by(TranscriptEntry.timestamp_ms)
        )
        return list(result.scalars().all())
