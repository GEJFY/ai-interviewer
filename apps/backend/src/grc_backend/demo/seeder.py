"""Demo data seeder for AI Interview Tool."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from grc_backend.demo.data import DEMO_DATA, DEMO_PASSWORD, ORG_ID
from grc_core.database import DatabaseManager
from grc_core.models import (
    Interview,
    Interviewee,
    InterviewTask,
    KnowledgeItem,
    Organization,
    Project,
    Report,
    Template,
    TranscriptEntry,
    User,
)

logger = logging.getLogger(__name__)


def _hash_password(password: str) -> str:
    """Hash password using the same context as auth module."""
    from passlib.context import CryptContext

    ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return ctx.hash(password)


class DemoSeeder:
    """デモデータの投入・削除を行うシーダー。"""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    async def is_seeded(self) -> bool:
        """デモ組織が既に存在するか確認。"""
        async with self.db.session() as session:
            result = await session.execute(
                select(Organization).where(Organization.id == ORG_ID)
            )
            return result.scalar_one_or_none() is not None

    async def seed(self) -> dict:
        """全デモデータを投入。戻り値は投入件数サマリ。"""
        if await self.is_seeded():
            logger.info("Demo data already exists, skipping seed.")
            return {"status": "skipped", "message": "デモデータは既に投入済みです"}

        password_hash = _hash_password(DEMO_PASSWORD)
        counts: dict[str, int] = {}

        async with self.db.session() as session:
            # 1. Organization
            org_data = DEMO_DATA["organization"]
            session.add(Organization(**org_data))
            counts["organizations"] = 1

            # 2. Users
            for user_data in DEMO_DATA["users"]:
                session.add(User(**user_data, password_hash=password_hash))
            counts["users"] = len(DEMO_DATA["users"])

            # 3. Projects
            for proj_data in DEMO_DATA["projects"]:
                session.add(Project(**proj_data))
            counts["projects"] = len(DEMO_DATA["projects"])

            # 4. Templates
            for tpl_data in DEMO_DATA["templates"]:
                session.add(Template(**tpl_data))
            counts["templates"] = len(DEMO_DATA["templates"])

            # 5. Tasks
            for task_data in DEMO_DATA["tasks"]:
                session.add(InterviewTask(**task_data))
            counts["tasks"] = len(DEMO_DATA["tasks"])

            # 6. Interviewees
            for iee_data in DEMO_DATA["interviewees"]:
                session.add(Interviewee(**iee_data))
            counts["interviewees"] = len(DEMO_DATA["interviewees"])

            # 7. Interviews + TranscriptEntries
            interview_count = 0
            transcript_count = 0
            for itv_data in DEMO_DATA["interviews"]:
                transcript_entries = itv_data.pop("transcript", [])
                session.add(Interview(**itv_data))
                interview_count += 1

                for entry in transcript_entries:
                    session.add(
                        TranscriptEntry(
                            interview_id=itv_data["id"],
                            **entry,
                        )
                    )
                    transcript_count += 1

            counts["interviews"] = interview_count
            counts["transcript_entries"] = transcript_count

            # 8. Reports
            for rpt_data in DEMO_DATA["reports"]:
                session.add(Report(**rpt_data))
            counts["reports"] = len(DEMO_DATA["reports"])

            # 9. Knowledge Items
            for kn_data in DEMO_DATA["knowledge_items"]:
                session.add(KnowledgeItem(**kn_data))
            counts["knowledge_items"] = len(DEMO_DATA["knowledge_items"])

        logger.info(f"Demo data seeded successfully: {counts}")
        return {"status": "success", "counts": counts}

    async def reset(self) -> dict:
        """デモデータを削除して再投入。"""
        await self._delete_demo_data()
        return await self.seed()

    async def _delete_demo_data(self) -> None:
        """デモデータをFK順に削除。"""
        async with self.db.session() as session:
            # FK依存の逆順で削除
            await self._delete_by_org(session, KnowledgeItem)
            await self._delete_reports(session)
            await self._delete_transcripts(session)
            await self._delete_interviews(session)
            await self._delete_by_org(session, Interviewee)
            await self._delete_tasks(session)
            await self._delete_by_org(session, Template)
            await self._delete_projects(session)
            await self._delete_users(session)
            await session.execute(
                select(Organization).where(Organization.id == ORG_ID)
            )
            result = await session.execute(
                select(Organization).where(Organization.id == ORG_ID)
            )
            org = result.scalar_one_or_none()
            if org:
                await session.delete(org)

        logger.info("Demo data deleted successfully.")

    async def _delete_by_org(self, session: AsyncSession, model: type) -> None:
        """organization_idでフィルタして削除。"""
        result = await session.execute(
            select(model).where(model.organization_id == ORG_ID)
        )
        for obj in result.scalars().all():
            await session.delete(obj)

    async def _delete_reports(self, session: AsyncSession) -> None:
        """デモタスクに紐づくレポートを削除。"""
        task_ids = [t["id"] for t in DEMO_DATA["tasks"]]
        result = await session.execute(
            select(Report).where(Report.task_id.in_(task_ids))
        )
        for obj in result.scalars().all():
            await session.delete(obj)

    async def _delete_transcripts(self, session: AsyncSession) -> None:
        """デモインタビューに紐づくトランスクリプトを削除。"""
        interview_ids = [i["id"] for i in DEMO_DATA["interviews"]]
        result = await session.execute(
            select(TranscriptEntry).where(
                TranscriptEntry.interview_id.in_(interview_ids)
            )
        )
        for obj in result.scalars().all():
            await session.delete(obj)

    async def _delete_interviews(self, session: AsyncSession) -> None:
        """デモタスクに紐づくインタビューを削除。"""
        task_ids = [t["id"] for t in DEMO_DATA["tasks"]]
        result = await session.execute(
            select(Interview).where(Interview.task_id.in_(task_ids))
        )
        for obj in result.scalars().all():
            await session.delete(obj)

    async def _delete_tasks(self, session: AsyncSession) -> None:
        """デモプロジェクトに紐づくタスクを削除。"""
        project_ids = [p["id"] for p in DEMO_DATA["projects"]]
        result = await session.execute(
            select(InterviewTask).where(InterviewTask.project_id.in_(project_ids))
        )
        for obj in result.scalars().all():
            await session.delete(obj)

    async def _delete_projects(self, session: AsyncSession) -> None:
        """デモ組織に紐づくプロジェクトを削除。"""
        result = await session.execute(
            select(Project).where(Project.organization_id == ORG_ID)
        )
        for obj in result.scalars().all():
            await session.delete(obj)

    async def _delete_users(self, session: AsyncSession) -> None:
        """デモ組織に紐づくユーザーを削除。"""
        result = await session.execute(
            select(User).where(User.organization_id == ORG_ID)
        )
        for obj in result.scalars().all():
            await session.delete(obj)

    async def get_status(self) -> dict:
        """デモデータの状態を確認。"""
        if not await self.is_seeded():
            return {"seeded": False}

        async with self.db.session() as session:
            counts = {}
            counts["users"] = len(
                (
                    await session.execute(
                        select(User).where(User.organization_id == ORG_ID)
                    )
                )
                .scalars()
                .all()
            )
            counts["projects"] = len(
                (
                    await session.execute(
                        select(Project).where(Project.organization_id == ORG_ID)
                    )
                )
                .scalars()
                .all()
            )

            task_ids = [t["id"] for t in DEMO_DATA["tasks"]]
            counts["interviews"] = len(
                (
                    await session.execute(
                        select(Interview).where(Interview.task_id.in_(task_ids))
                    )
                )
                .scalars()
                .all()
            )

        return {"seeded": True, "counts": counts}
