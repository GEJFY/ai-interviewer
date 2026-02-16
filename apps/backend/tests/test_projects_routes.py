"""プロジェクトルートのユニットテスト。

テスト対象: apps/backend/src/grc_backend/api/routes/projects.py
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
from grc_backend.api.routes import projects
from grc_core.enums import ProjectStatus

# --- テスト用ヘルパー ---


def _make_user(role="manager", org_id="org-1"):
    """テスト用ユーザーモック。"""
    user = MagicMock()
    user.id = "user-1"
    user.role = role
    user.organization_id = org_id
    return user


def _make_project(project_id="proj-1", org_id="org-1", status_val=ProjectStatus.ACTIVE):
    """テスト用プロジェクトモック。"""
    proj = MagicMock()
    proj.id = project_id
    proj.name = "Test Project"
    proj.description = "Description"
    proj.client_name = "Client A"
    proj.start_date = None
    proj.end_date = None
    proj.organization_id = org_id
    proj.created_by = "user-1"
    proj.status = status_val
    proj.created_at = datetime(2025, 1, 1)
    proj.updated_at = datetime(2025, 1, 1)
    return proj


def _create_app(user):
    """テスト用 FastAPI アプリ (依存関数をオーバーライド)。"""
    app = FastAPI()
    app.include_router(projects.router, prefix="/projects")
    app.dependency_overrides[get_db] = lambda: AsyncMock()
    app.dependency_overrides[get_current_active_user] = lambda: user
    app.dependency_overrides[require_manager_or_admin] = lambda: user
    return app


# --- list_projects テスト ---


class TestListProjects:
    """GET /projects のテスト。"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.user = _make_user()
        self.app = _create_app(self.user)
        self.client = TestClient(self.app)

    @patch("grc_backend.api.routes.projects.ProjectRepository")
    def test_list_projects_success(self, mock_repo_cls):
        """プロジェクト一覧が返ること。"""
        project = _make_project()
        repo = AsyncMock()
        repo.get_multi.return_value = [project]
        repo.count.return_value = 1
        repo.get_task_counts.return_value = {"total": 3, "completed": 1}
        mock_repo_cls.return_value = repo

        resp = self.client.get("/projects")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Test Project"

    @patch("grc_backend.api.routes.projects.ProjectRepository")
    def test_list_projects_empty(self, mock_repo_cls):
        """プロジェクトがない場合に空リストが返ること。"""
        repo = AsyncMock()
        repo.get_multi.return_value = []
        repo.count.return_value = 0
        mock_repo_cls.return_value = repo

        resp = self.client.get("/projects")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["total"] == 0


# --- create_project テスト ---


class TestCreateProject:
    """POST /projects のテスト。"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.user = _make_user()
        self.app = _create_app(self.user)
        self.client = TestClient(self.app)

    @patch("grc_backend.api.routes.projects.ProjectRepository")
    def test_create_project_success(self, mock_repo_cls):
        """プロジェクト作成が成功すること。"""
        project = _make_project()
        repo = AsyncMock()
        repo.create.return_value = project
        mock_repo_cls.return_value = repo

        resp = self.client.post("/projects", json={"name": "New Project"})
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.json()["name"] == "Test Project"


# --- get_project テスト ---


class TestGetProject:
    """GET /projects/{project_id} のテスト。"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.user = _make_user()
        self.app = _create_app(self.user)
        self.client = TestClient(self.app)

    @patch("grc_backend.api.routes.projects.ProjectRepository")
    def test_get_project_success(self, mock_repo_cls):
        """プロジェクト取得が成功すること。"""
        project = _make_project()
        repo = AsyncMock()
        repo.get_with_tasks.return_value = project
        repo.get_task_counts.return_value = {"total": 2, "completed": 0}
        mock_repo_cls.return_value = repo

        resp = self.client.get("/projects/proj-1")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["id"] == "proj-1"

    @patch("grc_backend.api.routes.projects.ProjectRepository")
    def test_get_project_not_found(self, mock_repo_cls):
        """存在しないプロジェクトで404が返ること。"""
        repo = AsyncMock()
        repo.get_with_tasks.return_value = None
        mock_repo_cls.return_value = repo

        resp = self.client.get("/projects/nonexistent")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    @patch("grc_backend.api.routes.projects.ProjectRepository")
    def test_get_project_access_denied(self, mock_repo_cls):
        """他組織のプロジェクトで403が返ること。"""
        project = _make_project(org_id="other-org")
        repo = AsyncMock()
        repo.get_with_tasks.return_value = project
        mock_repo_cls.return_value = repo

        resp = self.client.get("/projects/proj-1")
        assert resp.status_code == status.HTTP_403_FORBIDDEN


# --- update_project テスト ---


class TestUpdateProject:
    """PUT /projects/{project_id} のテスト。"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.user = _make_user()
        self.app = _create_app(self.user)
        self.client = TestClient(self.app)

    @patch("grc_backend.api.routes.projects.ProjectRepository")
    def test_update_project_success(self, mock_repo_cls):
        """プロジェクト更新が成功すること。"""
        project = _make_project()
        updated = _make_project()
        updated.name = "Updated Name"
        repo = AsyncMock()
        repo.get.return_value = project
        repo.update.return_value = updated
        mock_repo_cls.return_value = repo

        resp = self.client.put("/projects/proj-1", json={"name": "Updated Name"})
        assert resp.status_code == status.HTTP_200_OK

    @patch("grc_backend.api.routes.projects.ProjectRepository")
    def test_update_project_not_found(self, mock_repo_cls):
        """存在しないプロジェクト更新で404が返ること。"""
        repo = AsyncMock()
        repo.get.return_value = None
        mock_repo_cls.return_value = repo

        resp = self.client.put("/projects/nonexistent", json={"name": "X"})
        assert resp.status_code == status.HTTP_404_NOT_FOUND


# --- delete_project テスト ---


class TestDeleteProject:
    """DELETE /projects/{project_id} のテスト。"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.user = _make_user()
        self.app = _create_app(self.user)
        self.client = TestClient(self.app)

    @patch("grc_backend.api.routes.projects.ProjectRepository")
    def test_delete_project_success(self, mock_repo_cls):
        """プロジェクト削除(アーカイブ)が成功すること。"""
        project = _make_project()
        repo = AsyncMock()
        repo.get.return_value = project
        repo.update.return_value = project
        mock_repo_cls.return_value = repo

        resp = self.client.delete("/projects/proj-1")
        assert resp.status_code == status.HTTP_204_NO_CONTENT

    @patch("grc_backend.api.routes.projects.ProjectRepository")
    def test_delete_project_not_found(self, mock_repo_cls):
        """存在しないプロジェクト削除で404が返ること。"""
        repo = AsyncMock()
        repo.get.return_value = None
        mock_repo_cls.return_value = repo

        resp = self.client.delete("/projects/nonexistent")
        assert resp.status_code == status.HTTP_404_NOT_FOUND
