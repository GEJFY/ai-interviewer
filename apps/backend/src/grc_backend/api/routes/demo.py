"""Demo data management endpoints (development only)."""

import logging

from fastapi import APIRouter, HTTPException

from grc_backend.api.deps import DBSession
from grc_backend.config import get_settings
from grc_backend.demo.seeder import DemoSeeder
from grc_core.database import get_database

logger = logging.getLogger(__name__)

router = APIRouter()


def _require_non_production() -> None:
    """production環境でのアクセスをブロック。"""
    settings = get_settings()
    if settings.is_production:
        raise HTTPException(
            status_code=403,
            detail="Demo endpoints are not available in production.",
        )


@router.post("/seed")
async def seed_demo_data(db: DBSession) -> dict:
    """デモデータを投入（development/staging環境のみ）。"""
    _require_non_production()
    database = get_database()
    seeder = DemoSeeder(database)
    return await seeder.seed()


@router.post("/reset")
async def reset_demo_data(db: DBSession) -> dict:
    """デモデータをリセット（development/staging環境のみ）。"""
    _require_non_production()
    database = get_database()
    seeder = DemoSeeder(database)
    return await seeder.reset()


@router.get("/status")
async def demo_status(db: DBSession) -> dict:
    """デモデータの状態を確認。"""
    _require_non_production()
    database = get_database()
    seeder = DemoSeeder(database)
    return await seeder.get_status()
