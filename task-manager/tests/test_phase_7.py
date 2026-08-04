"""阶段 7：API 认证和分页测试。"""

import secrets
from datetime import datetime, timedelta

from models.project import Project
from models.task import Task
from storage.json_storage import JSONStorage
from web_app import app


def test_api_requires_bearer_token_when_configured(tmp_path, monkeypatch):
    token = secrets.token_urlsafe(24)
    monkeypatch.setenv("TASK_MANAGER_API_TOKEN", token)
    storage = JSONStorage(tmp_path / "tasks.json")
    storage.add(Task(title="受保护任务"))
    monkeypatch.setattr("routes.api_routes.JSONStorage", lambda: storage)
    client = app.test_client()

    assert client.get("/api/v1/health").status_code == 200

    unauthorized = client.get("/api/v1/tasks")
    assert unauthorized.status_code == 401
    assert unauthorized.get_json()["error"]["code"] == "authentication_required"
    assert unauthorized.headers["WWW-Authenticate"] == "Bearer"

    invalid = client.get("/api/v1/tasks", headers={"Authorization": "Bearer invalid"})
    assert invalid.status_code == 401

    authorized = client.get(
        "/api/v1/tasks",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert authorized.status_code == 200
    assert authorized.get_json()["meta"]["total"] == 1


def test_task_and_project_collections_support_pagination(tmp_path, monkeypatch):
    monkeypatch.delenv("TASK_MANAGER_API_TOKEN", raising=False)
    storage = JSONStorage(tmp_path / "tasks.json")
    base_time = datetime(2026, 8, 1, 9, 0)
    for index in range(5):
        storage.add(
            Task(
                title=f"分页任务 {index + 1}",
                created_at=base_time + timedelta(days=index),
                updated_at=base_time + timedelta(days=index),
            )
        )
    for index in range(3):
        storage.add_project(Project(name=f"分页项目 {index + 1}"))
    monkeypatch.setattr("routes.api_routes.JSONStorage", lambda: storage)
    client = app.test_client()

    task_response = client.get("/api/v1/tasks?page=2&page_size=2&sort_by=id")
    task_payload = task_response.get_json()
    assert task_response.status_code == 200
    assert [item["title"] for item in task_payload["data"]] == ["分页任务 3", "分页任务 4"]
    assert task_payload["meta"] == {
        "page": 2,
        "page_size": 2,
        "pages": 3,
        "total": 5,
        "count": 5,
        "returned": 2,
    }

    project_response = client.get("/api/v1/projects?page=2&page_size=2")
    project_payload = project_response.get_json()
    assert project_response.status_code == 200
    assert [item["name"] for item in project_payload["data"]] == ["分页项目 3"]
    assert project_payload["meta"]["pages"] == 2
    assert project_payload["meta"]["returned"] == 1

    invalid = client.get("/api/v1/tasks?page=0&page_size=2")
    assert invalid.status_code == 400
    assert invalid.get_json()["error"]["code"] == "invalid_request"


def test_project_detail_paginates_related_tasks(tmp_path, monkeypatch):
    monkeypatch.delenv("TASK_MANAGER_API_TOKEN", raising=False)
    storage = JSONStorage(tmp_path / "tasks.json")
    project = storage.add_project(Project(name="详情项目"))
    for index in range(3):
        storage.add(Task(title=f"详情任务 {index + 1}", project_id=project.id))
    monkeypatch.setattr("routes.api_routes.JSONStorage", lambda: storage)

    response = app.test_client().get(f"/api/v1/projects/{project.id}?page=2&page_size=2")
    payload = response.get_json()

    assert response.status_code == 200
    assert [task["title"] for task in payload["data"]["tasks"]] == ["详情任务 3"]
    assert payload["meta"]["total"] == 3
    assert payload["meta"]["returned"] == 1
