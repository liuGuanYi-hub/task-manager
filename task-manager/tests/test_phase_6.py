"""阶段 6：SQLite、存储工厂和 REST API 测试。"""

import json

import pytest
from click.testing import CliRunner

from commands.storage import migrate_sqlite
from models.project import Project
from models.saved_view import SavedView
from models.task import Priority, Status, Task
from storage.factory import create_storage
from storage.json_storage import JSONStorage
from storage.sqlite_storage import SQLiteStorage
from web_app import app


@pytest.fixture(autouse=True)
def disable_api_token_for_phase_6_tests(monkeypatch):
    monkeypatch.delenv("TASK_MANAGER_API_TOKEN", raising=False)


def test_sqlite_persists_all_entities_and_archive_state(tmp_path):
    path = tmp_path / "tasks.db"
    storage = SQLiteStorage(path)
    project = storage.add_project(Project(name="SQLite 项目"))
    task = storage.add(
        Task(
            title="SQLite 任务",
            priority=Priority.HIGH,
            status=Status.IN_PROGRESS,
            tags=["数据库"],
            project_id=project.id,
        )
    )
    storage.add_saved_view(SavedView(name="SQLite 视图", filters={"project_id": project.id}))
    storage.archive(task.id)

    reloaded = SQLiteStorage(path)
    saved_task = reloaded.get_by_id(task.id)
    assert saved_task is not None
    assert saved_task.archived is True
    assert saved_task.project_id == project.id
    assert saved_task.tags == ["数据库"]
    assert reloaded.get_project_by_id(project.id).name == "SQLite 项目"
    assert reloaded.get_saved_views()[0].filters["project_id"] == project.id


def test_json_to_sqlite_migration_is_repeatable(tmp_path):
    json_path = tmp_path / "source.json"
    sqlite_path = tmp_path / "target.db"
    source = JSONStorage(json_path)
    project = source.add_project(Project(name="迁移项目"))
    task = source.add(Task(title="迁移任务", project_id=project.id))
    source.archive(task.id)
    source.add_saved_view(SavedView(name="迁移视图", filters={"project_id": project.id}))

    first, first_result = SQLiteStorage.migrate_from_json(json_path, sqlite_path)
    second, second_result = SQLiteStorage.migrate_from_json(json_path, sqlite_path)

    assert first_result["tasks"] == 1
    assert second_result["tasks"] == 1
    assert len(second.get_all(include_archived=True)) == 1
    assert len(second.get_projects()) == 1
    assert len(second.get_saved_views()) == 1
    assert second.get_by_id(task.id).archived is True
    assert first.export_payload()["total_tasks"] == second.export_payload()["total_tasks"]


def test_storage_factory_switches_backend_without_changing_default(tmp_path, monkeypatch):
    monkeypatch.delenv("TASK_MANAGER_STORAGE", raising=False)
    json_storage = create_storage(str(tmp_path / "tasks.json"))
    assert isinstance(json_storage, JSONStorage)

    monkeypatch.setenv("TASK_MANAGER_STORAGE", "sqlite")
    sqlite_storage = create_storage(str(tmp_path / "tasks.db"))
    assert isinstance(sqlite_storage, SQLiteStorage)
    sqlite_storage.add(Task(title="工厂任务"))
    assert SQLiteStorage(tmp_path / "tasks.db").get_all()[0].title == "工厂任务"


def test_cli_migrate_sqlite_command(tmp_path):
    json_path = tmp_path / "tasks.json"
    sqlite_path = tmp_path / "tasks.db"
    storage = JSONStorage(json_path)
    storage.add(Task(title="CLI 迁移任务"))

    result = CliRunner().invoke(
        migrate_sqlite,
        [str(json_path), "--sqlite-path", str(sqlite_path)],
    )

    assert result.exit_code == 0
    assert "SQLite 迁移完成" in result.output
    assert SQLiteStorage(sqlite_path).get_all()[0].title == "CLI 迁移任务"


def test_rest_api_uses_shared_storage_business_methods(tmp_path, monkeypatch):
    storage = SQLiteStorage(tmp_path / "api.db")
    monkeypatch.setattr("routes.api_routes.JSONStorage", lambda: storage)
    client = app.test_client()

    project_response = client.post("/api/v1/projects", json={"name": "API 项目"})
    assert project_response.status_code == 201
    project = project_response.get_json()["data"]

    task_response = client.post(
        "/api/v1/tasks",
        json={
            "title": "API 任务",
            "priority": Priority.HIGH.value,
            "project_id": project["id"],
            "tags": ["接口"],
        },
    )
    assert task_response.status_code == 201
    task = task_response.get_json()["data"]
    assert task["project_name"] == "API 项目"

    patched = client.patch(
        f"/api/v1/tasks/{task['id']}",
        json={"status": Status.DONE.value},
    )
    assert patched.status_code == 200
    assert patched.get_json()["data"]["status"] == Status.DONE.value

    archived = client.delete(f"/api/v1/tasks/{task['id']}")
    assert archived.status_code == 200
    assert archived.get_json()["data"]["archived"] is True
    assert client.get("/api/v1/tasks").get_json()["meta"]["count"] == 0
    assert client.get("/api/v1/tasks?include_archived=1").get_json()["meta"]["count"] == 1

    invalid = client.post("/api/v1/tasks", json={"title": ""})
    assert invalid.status_code == 400
    assert invalid.get_json()["error"]["code"] == "invalid_request"


def test_api_health_reports_selected_backend(tmp_path, monkeypatch):
    storage = SQLiteStorage(tmp_path / "health.db")
    monkeypatch.setattr("routes.api_routes.JSONStorage", lambda: storage)

    response = app.test_client().get("/api/v1/health")

    assert response.status_code == 200
    assert response.get_json()["data"]["backend"] == "sqlite"
