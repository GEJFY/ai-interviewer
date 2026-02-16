"""テンプレートルートのユニットテスト。

テスト対象: apps/backend/src/grc_backend/api/routes/templates.py
依存関係をモックして各エンドポイントの正常系/異常系をテスト。
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from grc_backend.api.deps import (
    get_current_active_user,
    get_db,
    require_manager_or_admin,
)
from grc_backend.api.routes import templates
from grc_core.enums import UseCaseType

# --- テスト用ヘルパー ---


def _make_user(role="manager", org_id="org-1"):
    user = MagicMock()
    user.id = "user-1"
    user.role = role
    user.organization_id = org_id
    return user


def _make_template(template_id="tmpl-1", org_id="org-1", published=False):
    tmpl = MagicMock()
    tmpl.id = template_id
    tmpl.name = "Test Template"
    tmpl.description = "Template description"
    tmpl.use_case_type = UseCaseType.PROCESS_REVIEW
    tmpl.organization_id = org_id
    tmpl.created_by = "user-1"
    tmpl.questions = [{"order": 1, "question": "Q1", "required": True}]
    tmpl.settings = {}
    tmpl.version = 1
    tmpl.is_published = published
    tmpl.created_at = datetime(2025, 1, 1)
    tmpl.updated_at = datetime(2025, 1, 1)
    return tmpl


def _create_app(user):
    app = FastAPI()
    app.include_router(templates.router, prefix="/templates")
    app.dependency_overrides[get_db] = lambda: AsyncMock()
    app.dependency_overrides[get_current_active_user] = lambda: user
    app.dependency_overrides[require_manager_or_admin] = lambda: user
    return app


# --- list_templates テスト ---


class TestListTemplates:
    """GET /templates のテスト。"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.user = _make_user()
        self.app = _create_app(self.user)
        self.client = TestClient(self.app)

    @patch("grc_backend.api.routes.templates.TemplateRepository")
    def test_list_templates_success(self, mock_repo_cls):
        """テンプレート一覧が返ること。"""
        tmpl = _make_template()
        repo = AsyncMock()
        repo.get_by_organization.return_value = [tmpl]
        repo.count.return_value = 1
        mock_repo_cls.return_value = repo

        resp = self.client.get("/templates")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "Test Template"

    @patch("grc_backend.api.routes.templates.TemplateRepository")
    def test_list_templates_no_org(self, mock_repo_cls):
        """organization_idがないユーザーでpublishedテンプレートが返ること。"""
        user_no_org = _make_user(org_id=None)
        app = _create_app(user_no_org)
        repo = AsyncMock()
        repo.get_published.return_value = []
        mock_repo_cls.return_value = repo

        client = TestClient(app)
        resp = client.get("/templates")
        assert resp.status_code == status.HTTP_200_OK


# --- create_template テスト ---


class TestCreateTemplate:
    """POST /templates のテスト。"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.user = _make_user()
        self.app = _create_app(self.user)
        self.client = TestClient(self.app)

    @patch("grc_backend.api.routes.templates.TemplateRepository")
    def test_create_template_success(self, mock_repo_cls):
        """テンプレート作成が成功すること。"""
        tmpl = _make_template()
        repo = AsyncMock()
        repo.create.return_value = tmpl
        mock_repo_cls.return_value = repo

        resp = self.client.post(
            "/templates",
            json={
                "name": "New Template",
                "use_case_type": "process_review",
                "questions": [{"order": 1, "question": "First question?", "required": True}],
            },
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.json()["name"] == "Test Template"


# --- get_template テスト ---


class TestGetTemplate:
    """GET /templates/{template_id} のテスト。"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.user = _make_user()
        self.app = _create_app(self.user)
        self.client = TestClient(self.app)

    @patch("grc_backend.api.routes.templates.TemplateRepository")
    def test_get_template_success(self, mock_repo_cls):
        """テンプレート取得が成功すること。"""
        tmpl = _make_template()
        repo = AsyncMock()
        repo.get.return_value = tmpl
        mock_repo_cls.return_value = repo

        resp = self.client.get("/templates/tmpl-1")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["id"] == "tmpl-1"

    @patch("grc_backend.api.routes.templates.TemplateRepository")
    def test_get_template_not_found(self, mock_repo_cls):
        """存在しないテンプレートで404が返ること。"""
        repo = AsyncMock()
        repo.get.return_value = None
        mock_repo_cls.return_value = repo

        resp = self.client.get("/templates/nonexistent")
        assert resp.status_code == status.HTTP_404_NOT_FOUND


# --- update_template テスト ---


class TestUpdateTemplate:
    """PUT /templates/{template_id} のテスト。"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.user = _make_user()
        self.app = _create_app(self.user)
        self.client = TestClient(self.app)

    @patch("grc_backend.api.routes.templates.TemplateRepository")
    def test_update_template_success(self, mock_repo_cls):
        """テンプレート更新が成功すること。"""
        tmpl = _make_template()
        updated = _make_template()
        updated.name = "Updated Template"
        updated.version = 2
        repo = AsyncMock()
        repo.get.return_value = tmpl
        repo.update.return_value = updated
        mock_repo_cls.return_value = repo

        resp = self.client.put("/templates/tmpl-1", json={"name": "Updated Template"})
        assert resp.status_code == status.HTTP_200_OK

    @patch("grc_backend.api.routes.templates.TemplateRepository")
    def test_update_template_not_found(self, mock_repo_cls):
        """存在しないテンプレート更新で404が返ること。"""
        repo = AsyncMock()
        repo.get.return_value = None
        mock_repo_cls.return_value = repo

        resp = self.client.put("/templates/nonexistent", json={"name": "X"})
        assert resp.status_code == status.HTTP_404_NOT_FOUND


# --- clone_template テスト ---


class TestCloneTemplate:
    """POST /templates/{template_id}/clone のテスト。"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.user = _make_user()
        self.app = _create_app(self.user)
        self.client = TestClient(self.app)

    @patch("grc_backend.api.routes.templates.TemplateRepository")
    def test_clone_template_success(self, mock_repo_cls):
        """テンプレートクローンが成功すること。"""
        cloned = _make_template(template_id="tmpl-2")
        cloned.name = "Test Template (Copy)"
        repo = AsyncMock()
        repo.clone.return_value = cloned
        mock_repo_cls.return_value = repo

        resp = self.client.post("/templates/tmpl-1/clone")
        assert resp.status_code == status.HTTP_200_OK

    @patch("grc_backend.api.routes.templates.TemplateRepository")
    def test_clone_template_not_found(self, mock_repo_cls):
        """存在しないテンプレートクローンで404が返ること。"""
        repo = AsyncMock()
        repo.clone.return_value = None
        mock_repo_cls.return_value = repo

        resp = self.client.post("/templates/nonexistent/clone")
        assert resp.status_code == status.HTTP_404_NOT_FOUND


# --- publish / unpublish テスト ---


class TestPublishUnpublish:
    """POST /templates/{id}/publish, /unpublish のテスト。"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.user = _make_user()
        self.app = _create_app(self.user)
        self.client = TestClient(self.app)

    @patch("grc_backend.api.routes.templates.TemplateRepository")
    def test_publish_success(self, mock_repo_cls):
        """テンプレート公開が成功すること。"""
        tmpl = _make_template(published=True)
        repo = AsyncMock()
        repo.publish.return_value = tmpl
        mock_repo_cls.return_value = repo

        resp = self.client.post("/templates/tmpl-1/publish")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["is_published"] is True

    @patch("grc_backend.api.routes.templates.TemplateRepository")
    def test_publish_not_found(self, mock_repo_cls):
        """存在しないテンプレート公開で404が返ること。"""
        repo = AsyncMock()
        repo.publish.return_value = None
        mock_repo_cls.return_value = repo

        resp = self.client.post("/templates/nonexistent/publish")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    @patch("grc_backend.api.routes.templates.TemplateRepository")
    def test_unpublish_success(self, mock_repo_cls):
        """テンプレート非公開が成功すること。"""
        tmpl = _make_template(published=False)
        repo = AsyncMock()
        repo.unpublish.return_value = tmpl
        mock_repo_cls.return_value = repo

        resp = self.client.post("/templates/tmpl-1/unpublish")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["is_published"] is False


# --- delete_template テスト ---


class TestDeleteTemplate:
    """DELETE /templates/{template_id} のテスト。"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.user = _make_user()
        self.app = _create_app(self.user)
        self.client = TestClient(self.app)

    @patch("grc_backend.api.routes.templates.TemplateRepository")
    def test_delete_template_success(self, mock_repo_cls):
        """テンプレート削除が成功すること。"""
        repo = AsyncMock()
        repo.exists.return_value = True
        repo.delete.return_value = None
        mock_repo_cls.return_value = repo

        resp = self.client.delete("/templates/tmpl-1")
        assert resp.status_code == status.HTTP_204_NO_CONTENT

    @patch("grc_backend.api.routes.templates.TemplateRepository")
    def test_delete_template_not_found(self, mock_repo_cls):
        """存在しないテンプレート削除で404が返ること。"""
        repo = AsyncMock()
        repo.exists.return_value = False
        mock_repo_cls.return_value = repo

        resp = self.client.delete("/templates/nonexistent")
        assert resp.status_code == status.HTTP_404_NOT_FOUND
