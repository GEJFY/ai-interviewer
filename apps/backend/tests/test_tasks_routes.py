"""タスクルートのユニットテスト。

テスト対象: apps/backend/src/grc_backend/api/routes/tasks.py
依存関係をモックして各エンドポイントの正常系/異常系をテスト。
"""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from grc_backend.api.deps import (
    get_current_active_user,
    get_db,
    require_manager_or_admin,
)
from grc_backend.api.routes import tasks
from grc_core.enums import TaskStatus, UseCaseType

# --- テスト用ヘルパー ---


def _make_user(role="manager", org_id="org-1"):
    user = MagicMock()
    user.id = "user-1"
    user.role = role
    user.organization_id = org_id
    return user


def _make_task(task_id="task-1", project_id="proj-1"):
    """テスト用タスクモック（SimpleNamespaceでcamelCase属性の自動生成を防止）。"""
    return SimpleNamespace(
        id=task_id,
        name="Test Task",
        description="Task description",
        use_case_type=UseCaseType.PROCESS_REVIEW,
        target_count=3,
        deadline=None,
        project_id=project_id,
        template_id=None,
        created_by="user-1",
        status=TaskStatus.PENDING,
        settings={},
        created_at=datetime(2025, 1, 1),
        updated_at=datetime(2025, 1, 1),
    )


def _make_project(project_id="proj-1", org_id="org-1"):
    return SimpleNamespace(
        id=project_id,
        organization_id=org_id,
    )


def _create_app(user):
    app = FastAPI()
    app.include_router(tasks.router, prefix="/tasks")
    app.dependency_overrides[get_db] = lambda: AsyncMock()
    app.dependency_overrides[get_current_active_user] = lambda: user
    app.dependency_overrides[require_manager_or_admin] = lambda: user
    return app


# --- list_tasks テスト ---


class TestListTasks:
    """GET /tasks のテスト。"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.user = _make_user()
        self.app = _create_app(self.user)
        self.client = TestClient(self.app)

    @patch("grc_backend.api.routes.tasks.TaskRepository")
    def test_list_tasks_success(self, mock_repo_cls):
        """タスク一覧が返ること。"""
        task = _make_task()
        repo = AsyncMock()
        repo.get_multi.return_value = [task]
        repo.count.return_value = 1
        repo.get_interview_counts.return_value = {"total": 5, "completed": 2}
        mock_repo_cls.return_value = repo

        resp = self.client.get("/tasks")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "Test Task"

    @patch("grc_backend.api.routes.tasks.TaskRepository")
    def test_list_tasks_with_project_filter(self, mock_repo_cls):
        """project_idフィルタが適用されること。"""
        repo = AsyncMock()
        repo.get_multi.return_value = []
        repo.count.return_value = 0
        mock_repo_cls.return_value = repo

        resp = self.client.get("/tasks?project_id=proj-1")
        assert resp.status_code == status.HTTP_200_OK
        call_kwargs = repo.get_multi.call_args
        assert call_kwargs[1]["filters"]["project_id"] == "proj-1"


# --- create_task テスト ---


class TestCreateTask:
    """POST /tasks のテスト。"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.user = _make_user()
        self.app = _create_app(self.user)
        self.client = TestClient(self.app)

    @patch("grc_backend.api.routes.tasks.TaskRepository")
    @patch("grc_backend.api.routes.tasks.ProjectRepository")
    def test_create_task_success(self, mock_proj_cls, mock_task_cls):
        """タスク作成が成功すること。"""
        project = _make_project()
        mock_proj_cls.return_value = AsyncMock(get=AsyncMock(return_value=project))

        task = _make_task()
        mock_task_cls.return_value = AsyncMock(create=AsyncMock(return_value=task))

        resp = self.client.post(
            "/tasks",
            json={
                "name": "New Task",
                "use_case_type": "process_review",
                "project_id": "proj-1",
            },
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.json()["name"] == "Test Task"

    @patch("grc_backend.api.routes.tasks.ProjectRepository")
    def test_create_task_project_not_found(self, mock_proj_cls):
        """存在しないプロジェクトへのタスク作成で404が返ること。"""
        mock_proj_cls.return_value = AsyncMock(get=AsyncMock(return_value=None))

        resp = self.client.post(
            "/tasks",
            json={
                "name": "New Task",
                "use_case_type": "process_review",
                "project_id": "nonexistent",
            },
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    @patch("grc_backend.api.routes.tasks.ProjectRepository")
    def test_create_task_access_denied(self, mock_proj_cls):
        """他組織のプロジェクトへのタスク作成で403が返ること。"""
        project = _make_project(org_id="other-org")
        mock_proj_cls.return_value = AsyncMock(get=AsyncMock(return_value=project))

        resp = self.client.post(
            "/tasks",
            json={
                "name": "New Task",
                "use_case_type": "process_review",
                "project_id": "proj-1",
            },
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN


# --- get_task テスト ---


class TestGetTask:
    """GET /tasks/{task_id} のテスト。"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.user = _make_user()
        self.app = _create_app(self.user)
        self.client = TestClient(self.app)

    @patch("grc_backend.api.routes.tasks.TaskRepository")
    def test_get_task_success(self, mock_repo_cls):
        """タスク取得が成功すること。"""
        task = _make_task()
        repo = AsyncMock()
        repo.get_with_interviews.return_value = task
        repo.get_interview_counts.return_value = {"total": 1, "completed": 0}
        mock_repo_cls.return_value = repo

        resp = self.client.get("/tasks/task-1")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["id"] == "task-1"

    @patch("grc_backend.api.routes.tasks.TaskRepository")
    def test_get_task_not_found(self, mock_repo_cls):
        """存在しないタスクで404が返ること。"""
        repo = AsyncMock()
        repo.get_with_interviews.return_value = None
        mock_repo_cls.return_value = repo

        resp = self.client.get("/tasks/nonexistent")
        assert resp.status_code == status.HTTP_404_NOT_FOUND


# --- update_task テスト ---


class TestUpdateTask:
    """PUT /tasks/{task_id} のテスト。"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.user = _make_user()
        self.app = _create_app(self.user)
        self.client = TestClient(self.app)

    @patch("grc_backend.api.routes.tasks.TaskRepository")
    def test_update_task_success(self, mock_repo_cls):
        """タスク更新が成功すること。"""
        task = _make_task()
        updated = _make_task()
        updated.name = "Updated Task"
        repo = AsyncMock()
        repo.get.return_value = task
        repo.update.return_value = updated
        mock_repo_cls.return_value = repo

        resp = self.client.put("/tasks/task-1", json={"name": "Updated Task"})
        assert resp.status_code == status.HTTP_200_OK

    @patch("grc_backend.api.routes.tasks.TaskRepository")
    def test_update_task_not_found(self, mock_repo_cls):
        """存在しないタスク更新で404が返ること。"""
        repo = AsyncMock()
        repo.get.return_value = None
        mock_repo_cls.return_value = repo

        resp = self.client.put("/tasks/nonexistent", json={"name": "X"})
        assert resp.status_code == status.HTTP_404_NOT_FOUND


# --- delete_task テスト ---


class TestDeleteTask:
    """DELETE /tasks/{task_id} のテスト。"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.user = _make_user()
        self.app = _create_app(self.user)
        self.client = TestClient(self.app)

    @patch("grc_backend.api.routes.tasks.TaskRepository")
    def test_delete_task_success(self, mock_repo_cls):
        """タスク削除(キャンセル)が成功すること。"""
        task = _make_task()
        repo = AsyncMock()
        repo.get.return_value = task
        repo.update.return_value = task
        mock_repo_cls.return_value = repo

        resp = self.client.delete("/tasks/task-1")
        assert resp.status_code == status.HTTP_204_NO_CONTENT

    @patch("grc_backend.api.routes.tasks.TaskRepository")
    def test_delete_task_not_found(self, mock_repo_cls):
        """存在しないタスク削除で404が返ること。"""
        repo = AsyncMock()
        repo.get.return_value = None
        mock_repo_cls.return_value = repo

        resp = self.client.delete("/tasks/nonexistent")
        assert resp.status_code == status.HTTP_404_NOT_FOUND
