"""阶段 15.11：真实 SQLite 运行实例的 Web/API 错误契约。"""

import io

from models.project import Project
from models.task import Task
from storage.sqlite_storage import SQLiteStorage
from web_app import app


TEST_TOKEN = "test-only-token"


def _seed_sqlite(path):
    storage = SQLiteStorage(path)
    project = storage.add_project(Project(name="阶段 15.11 项目"))
    storage.add(Task(title="阶段 15.11 任务", project_id=project.id))
    return storage


def _auth_headers():
    return {"Authorization": f"Bearer {TEST_TOKEN}"}


def test_runtime_sqlite_web_and_api_contract(tmp_path, monkeypatch):
    db_path = tmp_path / "runtime.db"
    storage = _seed_sqlite(db_path)
    before = db_path.read_bytes()
    monkeypatch.setenv("TASK_MANAGER_STORAGE", "sqlite")
    monkeypatch.setenv("TASK_MANAGER_SQLITE_PATH", str(db_path))
    monkeypatch.setenv("TASK_MANAGER_API_TOKEN", TEST_TOKEN)
    client = app.test_client()

    settings = client.get("/settings/")
    assert settings.status_code == 200
    settings_body = settings.get_data(as_text=True)
    assert "总任务数" in settings_body
    assert "项目数" in settings_body

    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.get_json()["data"] == {
        "status": "ok",
        "backend": "sqlite",
        "database": "runtime.db",
    }

    unauthorized = client.get("/api/v1/tasks")
    assert unauthorized.status_code == 401
    assert unauthorized.get_json()["error"]["code"] == "authentication_required"

    authorized = client.get("/api/v1/tasks?page=1&page_size=1", headers=_auth_headers())
    assert authorized.status_code == 200
    assert authorized.get_json()["meta"]["total"] == 1
    assert authorized.get_json()["data"][0]["title"] == "阶段 15.11 任务"

    invalid = client.post(
        "/api/v1/tasks",
        json={"title": ""},
        headers=_auth_headers(),
    )
    assert invalid.status_code == 400
    assert invalid.is_json
    assert invalid.get_json() == {
        "error": {"code": "invalid_request", "message": "title 不能为空"}
    }

    missing = client.get("/api/v1/not-a-real-resource", headers=_auth_headers())
    assert missing.status_code == 404
    assert missing.get_json() == {
        "error": {"code": "not_found", "message": "资源不存在"}
    }
    assert db_path.read_bytes() == before
    assert len(storage.get_all()) == 1


def test_runtime_sqlite_import_error_keeps_database_unchanged(tmp_path, monkeypatch):
    db_path = tmp_path / "import-errors.db"
    storage = _seed_sqlite(db_path)
    before = db_path.read_bytes()
    monkeypatch.setenv("TASK_MANAGER_STORAGE", "sqlite")
    monkeypatch.setenv("TASK_MANAGER_SQLITE_PATH", str(db_path))
    monkeypatch.delenv("TASK_MANAGER_API_TOKEN", raising=False)

    response = app.test_client().post(
        "/settings/import",
        data={
            "mode": "import",
            "conflict": "replace",
            "backup_file": (io.BytesIO(b""), "empty.json"),
        },
        content_type="multipart/form-data",
    )
    body = response.get_data(as_text=True)

    assert response.status_code == 400
    assert "导入文件不能为空" in body
    assert 'option value="replace" selected' in body
    assert db_path.read_bytes() == before
    assert len(storage.get_all()) == 1
