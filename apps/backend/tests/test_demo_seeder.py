"""デモデータシーダーのユニットテスト。

テスト対象:
  - apps/backend/src/grc_backend/demo/data.py
  - apps/backend/src/grc_backend/demo/seeder.py
  - apps/backend/src/grc_backend/api/routes/demo.py
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from grc_backend.demo.data import DEMO_DATA, DEMO_PASSWORD, ORG_ID

# --- データ定義の完全性テスト ---


class TestDemoDataCompleteness:
    """data.py の全データ定義が正しいか検証。"""

    def test_organization_exists(self):
        """組織データが定義されていること。"""
        org = DEMO_DATA["organization"]
        assert org["id"] == ORG_ID
        assert org["name"] == "テクノファイナンス株式会社"
        assert "settings" in org

    def test_users_count_and_roles(self):
        """4名のユーザーが全ロールで定義されていること。"""
        users = DEMO_DATA["users"]
        assert len(users) == 4
        roles = {u["role"] for u in users}
        assert roles == {"admin", "manager", "interviewer", "viewer"}

    def test_users_have_required_fields(self):
        """全ユーザーが必須フィールドを持つこと。"""
        for user in DEMO_DATA["users"]:
            assert user["id"]
            assert user["email"]
            assert user["name"]
            assert user["role"]
            assert user["organization_id"] == ORG_ID

    def test_users_emails_are_demo_domain(self):
        """全ユーザーのメールがdemo.example.comドメインであること。"""
        for user in DEMO_DATA["users"]:
            assert user["email"].endswith("@demo.example.com")

    def test_projects_count(self):
        """3件のプロジェクトが定義されていること。"""
        assert len(DEMO_DATA["projects"]) == 3

    def test_projects_have_required_fields(self):
        """全プロジェクトが必須フィールドを持つこと。"""
        for proj in DEMO_DATA["projects"]:
            assert proj["id"]
            assert proj["name"]
            assert proj["organization_id"] == ORG_ID
            assert proj["status"] in ("active", "completed", "archived")

    def test_templates_count(self):
        """4件のテンプレートが定義されていること。"""
        assert len(DEMO_DATA["templates"]) == 4

    def test_templates_have_questions(self):
        """全テンプレートに質問が含まれていること。"""
        for tpl in DEMO_DATA["templates"]:
            assert len(tpl["questions"]) > 0
            for q in tpl["questions"]:
                assert "order" in q
                assert "question" in q

    def test_tasks_count(self):
        """7件のタスクが定義されていること。"""
        assert len(DEMO_DATA["tasks"]) == 7

    def test_tasks_reference_valid_projects(self):
        """全タスクが有効なプロジェクトIDを参照していること。"""
        project_ids = {p["id"] for p in DEMO_DATA["projects"]}
        for task in DEMO_DATA["tasks"]:
            assert task["project_id"] in project_ids

    def test_tasks_status_distribution(self):
        """タスクに完了・進行中・予定の各ステータスが含まれること。"""
        statuses = {t["status"] for t in DEMO_DATA["tasks"]}
        assert "completed" in statuses
        assert "in_progress" in statuses
        assert "pending" in statuses

    def test_interviewees_count(self):
        """5名のインタビュー対象者が定義されていること。"""
        assert len(DEMO_DATA["interviewees"]) == 5

    def test_interviewees_include_anonymous(self):
        """匿名のインタビュー対象者が含まれること。"""
        anonymous = [i for i in DEMO_DATA["interviewees"] if i["is_anonymous"]]
        assert len(anonymous) >= 1

    def test_interviews_count(self):
        """5件のインタビューが定義されていること。"""
        assert len(DEMO_DATA["interviews"]) == 5

    def test_interviews_have_transcripts_when_completed(self):
        """完了インタビューにトランスクリプトが含まれること。"""
        for itv in DEMO_DATA["interviews"]:
            if itv["status"] == "completed":
                assert len(itv.get("transcript", [])) > 0, (
                    f"Interview {itv['id']} is completed but has no transcript"
                )

    def test_interviews_reference_valid_tasks(self):
        """全インタビューが有効なタスクIDを参照していること。"""
        task_ids = {t["id"] for t in DEMO_DATA["tasks"]}
        for itv in DEMO_DATA["interviews"]:
            assert itv["task_id"] in task_ids

    def test_completed_interviews_have_analysis(self):
        """完了インタビューにAI分析結果が含まれること。"""
        for itv in DEMO_DATA["interviews"]:
            if itv["status"] == "completed":
                assert itv["ai_analysis"] is not None
                assert "key_findings" in itv["ai_analysis"]
                assert "risks_identified" in itv["ai_analysis"]

    def test_reports_count(self):
        """5件のレポートが定義されていること。"""
        assert len(DEMO_DATA["reports"]) == 5

    def test_reports_have_varied_types(self):
        """複数種類のレポートが含まれること。"""
        types = {r["report_type"] for r in DEMO_DATA["reports"]}
        assert len(types) >= 3
        assert "process_doc" in types
        assert "rcm" in types

    def test_knowledge_items_count(self):
        """3件のナレッジが定義されていること。"""
        assert len(DEMO_DATA["knowledge_items"]) == 3

    def test_knowledge_items_have_tags(self):
        """全ナレッジにタグが設定されていること。"""
        for kn in DEMO_DATA["knowledge_items"]:
            assert kn["tags"] is not None
            assert len(kn["tags"]) > 0

    def test_demo_password_is_set(self):
        """デモパスワードが設定されていること。"""
        assert DEMO_PASSWORD == "demo1234"

    def test_all_ids_are_unique(self):
        """全IDがユニークであること。"""
        all_ids = []
        all_ids.append(DEMO_DATA["organization"]["id"])
        all_ids.extend(u["id"] for u in DEMO_DATA["users"])
        all_ids.extend(p["id"] for p in DEMO_DATA["projects"])
        all_ids.extend(t["id"] for t in DEMO_DATA["templates"])
        all_ids.extend(t["id"] for t in DEMO_DATA["tasks"])
        all_ids.extend(i["id"] for i in DEMO_DATA["interviewees"])
        all_ids.extend(i["id"] for i in DEMO_DATA["interviews"])
        all_ids.extend(r["id"] for r in DEMO_DATA["reports"])
        all_ids.extend(k["id"] for k in DEMO_DATA["knowledge_items"])
        assert len(all_ids) == len(set(all_ids)), "Duplicate IDs found"

    def test_transcript_entries_have_required_fields(self):
        """トランスクリプトエントリが必須フィールドを持つこと。"""
        for itv in DEMO_DATA["interviews"]:
            for entry in itv.get("transcript", []):
                assert entry["speaker"] in ("AI", "INTERVIEWEE", "INTERVIEWER")
                assert entry["content"]
                assert "timestamp_ms" in entry


# --- DemoSeeder テスト ---


class TestDemoSeeder:
    """DemoSeeder のユニットテスト。"""

    def _make_seeder(self):
        """モックDBを使用したDemoSeederを生成。"""
        from grc_backend.demo.seeder import DemoSeeder

        mock_db = MagicMock()
        return DemoSeeder(mock_db), mock_db

    @pytest.mark.asyncio
    async def test_is_seeded_returns_false_when_no_org(self):
        """組織が未投入の場合Falseを返すこと。"""
        seeder, mock_db = self._make_seeder()

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_session
        mock_ctx.__aexit__.return_value = None
        mock_db.session.return_value = mock_ctx

        result = await seeder.is_seeded()
        assert result is False

    @pytest.mark.asyncio
    async def test_is_seeded_returns_true_when_org_exists(self):
        """組織が投入済みの場合Trueを返すこと。"""
        seeder, mock_db = self._make_seeder()

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock()  # org exists
        mock_session.execute.return_value = mock_result

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_session
        mock_ctx.__aexit__.return_value = None
        mock_db.session.return_value = mock_ctx

        result = await seeder.is_seeded()
        assert result is True

    @pytest.mark.asyncio
    async def test_seed_skips_when_already_seeded(self):
        """デモデータが既に存在する場合はスキップすること。"""
        seeder, mock_db = self._make_seeder()

        with patch.object(seeder, "is_seeded", return_value=True):
            result = await seeder.seed()
            assert result["status"] == "skipped"


# --- Demo API テスト ---


class TestDemoApiEndpoints:
    """Demo APIエンドポイントのテスト。"""

    def test_require_non_production_blocks_production(self):
        """production環境でアクセスがブロックされること。"""
        from fastapi import HTTPException

        from grc_backend.api.routes.demo import _require_non_production

        with patch("grc_backend.api.routes.demo.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(is_production=True)
            with pytest.raises(HTTPException) as exc_info:
                _require_non_production()
            assert exc_info.value.status_code == 403

    def test_require_non_production_allows_development(self):
        """development環境でアクセスが許可されること。"""
        from grc_backend.api.routes.demo import _require_non_production

        with patch("grc_backend.api.routes.demo.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(is_production=False)
            _require_non_production()  # should not raise
