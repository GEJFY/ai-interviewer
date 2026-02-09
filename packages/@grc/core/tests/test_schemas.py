"""スキーマのユニットテスト。

テスト対象: packages/@grc/core/src/grc_core/schemas/
"""

import pytest
from pydantic import ValidationError

from grc_core.enums import (
    UseCaseType,
    UserRole,
)
from grc_core.schemas import (
    BaseSchema,
    InterviewCreate,
    KnowledgeSearchRequest,
    PaginatedResponse,
    ProjectCreate,
    TaskCreate,
    TemplateCreate,
    UserCreate,
)


# --- BaseSchema テスト ---


class TestBaseSchema:
    """BaseSchema のテスト。"""

    def test_from_attributes_enabled(self):
        """from_attributesが有効であること。"""
        assert BaseSchema.model_config.get("from_attributes") is True

    def test_populate_by_name_enabled(self):
        """populate_by_nameが有効であること。"""
        assert BaseSchema.model_config.get("populate_by_name") is True


# --- PaginatedResponse テスト ---


class TestPaginatedResponse:
    """PaginatedResponse のテスト。"""

    def test_construction(self):
        """正しく構築できること。"""
        resp = PaginatedResponse[str](
            items=["a", "b", "c"],
            total=10,
            page=1,
            page_size=3,
            pages=4,
        )
        assert len(resp.items) == 3
        assert resp.total == 10
        assert resp.page == 1
        assert resp.pages == 4

    def test_empty_items(self):
        """空のitemsで構築できること。"""
        resp = PaginatedResponse[str](
            items=[],
            total=0,
            page=1,
            page_size=10,
            pages=0,
        )
        assert resp.items == []
        assert resp.total == 0


# --- UserCreate テスト ---


class TestUserCreate:
    """UserCreate のテスト。"""

    def test_valid_user(self):
        """有効なユーザーが作成できること。"""
        user = UserCreate(
            email="test@example.com",
            name="テストユーザー",
            password="securepass123",
        )
        assert user.email == "test@example.com"
        assert user.name == "テストユーザー"

    def test_default_role(self):
        """デフォルトロールがviewerであること。"""
        user = UserCreate(email="test@example.com", name="Test")
        assert user.role == UserRole.VIEWER

    def test_invalid_email(self):
        """不正なメールが拒否されること。"""
        with pytest.raises(ValidationError):
            UserCreate(email="not-email", name="Test")

    def test_optional_password(self):
        """passwordがオプショナルであること（SSO用）。"""
        user = UserCreate(email="test@example.com", name="Test")
        assert user.password is None


# --- ProjectCreate テスト ---


class TestProjectCreate:
    """ProjectCreate のテスト。"""

    def test_valid_project(self):
        """有効なプロジェクトが作成できること。"""
        project = ProjectCreate(name="テストプロジェクト")
        assert project.name == "テストプロジェクト"

    def test_optional_description(self):
        """descriptionがオプショナルであること。"""
        project = ProjectCreate(name="Test")
        assert project.description is None

    def test_name_required(self):
        """nameが必須であること。"""
        with pytest.raises(ValidationError):
            ProjectCreate()


# --- TaskCreate テスト ---


class TestTaskCreate:
    """TaskCreate のテスト。"""

    def test_valid_task(self):
        """有効なタスクが作成できること。"""
        task = TaskCreate(
            name="テストタスク",
            project_id="proj-123",
            use_case_type=UseCaseType.COMPLIANCE_SURVEY,
        )
        assert task.name == "テストタスク"
        assert task.project_id == "proj-123"

    def test_default_target_count(self):
        """デフォルトtarget_countが1であること。"""
        task = TaskCreate(
            name="Test",
            project_id="p-1",
            use_case_type=UseCaseType.PROCESS_REVIEW,
        )
        assert task.target_count == 1

    def test_required_fields(self):
        """name, project_id, use_case_typeが必須であること。"""
        with pytest.raises(ValidationError):
            TaskCreate(name="Test")  # project_id, use_case_type不足


# --- InterviewCreate テスト ---


class TestInterviewCreate:
    """InterviewCreate のテスト。"""

    def test_valid_interview(self):
        """有効なインタビューが作成できること。"""
        interview = InterviewCreate(task_id="task-123")
        assert interview.task_id == "task-123"

    def test_default_language(self):
        """デフォルト言語がjaであること。"""
        interview = InterviewCreate(task_id="task-123")
        assert interview.language == "ja"

    def test_task_id_required(self):
        """task_idが必須であること。"""
        with pytest.raises(ValidationError):
            InterviewCreate()


# --- TemplateCreate テスト ---


class TestTemplateCreate:
    """TemplateCreate のテスト。"""

    def test_valid_template(self):
        """有効なテンプレートが作成できること。"""
        template = TemplateCreate(
            name="コンプライアンス調査テンプレート",
            use_case_type=UseCaseType.COMPLIANCE_SURVEY,
        )
        assert template.name == "コンプライアンス調査テンプレート"

    def test_required_fields(self):
        """name, use_case_typeが必須であること。"""
        with pytest.raises(ValidationError):
            TemplateCreate(name="Test")  # use_case_type不足


# --- KnowledgeSearchRequest テスト ---


class TestKnowledgeSearchRequest:
    """KnowledgeSearchRequest のテスト。"""

    def test_valid_search(self):
        """有効な検索リクエストが作成できること。"""
        req = KnowledgeSearchRequest(query="リスク管理について")
        assert req.query == "リスク管理について"

    def test_query_required(self):
        """queryが必須であること。"""
        with pytest.raises(ValidationError):
            KnowledgeSearchRequest()
