"""CLI commands for demo data management.

Usage:
    python -m grc_backend.demo seed    # デモデータ投入
    python -m grc_backend.demo reset   # デモデータリセット（削除→再投入）
    python -m grc_backend.demo status  # デモデータの状態確認
"""

import asyncio
import sys

from grc_backend.config import get_settings
from grc_backend.demo.seeder import DemoSeeder
from grc_core.database import DatabaseManager


async def _run(command: str) -> None:
    settings = get_settings()
    db = DatabaseManager(settings.database_url, echo=False)

    try:
        seeder = DemoSeeder(db)

        if command == "seed":
            print("デモデータを投入します...")
            result = await seeder.seed()
            if result["status"] == "skipped":
                print(f"  → {result['message']}")
            else:
                print("  → 投入完了:")
                for key, count in result["counts"].items():
                    print(f"    {key}: {count}件")

        elif command == "reset":
            print("デモデータをリセットします...")
            result = await seeder.reset()
            print("  → リセット完了:")
            for key, count in result["counts"].items():
                print(f"    {key}: {count}件")

        elif command == "status":
            status = await seeder.get_status()
            if not status["seeded"]:
                print("デモデータ: 未投入")
            else:
                print("デモデータ: 投入済み")
                for key, count in status["counts"].items():
                    print(f"  {key}: {count}件")

        else:
            print(f"Unknown command: {command}")
            print("Usage: python -m grc_backend.demo [seed|reset|status]")
            sys.exit(1)

    finally:
        await db.close()


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python -m grc_backend.demo [seed|reset|status]")
        sys.exit(1)

    command = sys.argv[1]
    asyncio.run(_run(command))


if __name__ == "__main__":
    main()
