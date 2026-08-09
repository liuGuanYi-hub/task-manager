from models.project import Project
from models.task import Task
from storage.json_storage import JSONStorage
from web_app import app


def test_search_endpoint_returns_real_tasks_projects_and_tags(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    project = storage.add_project(Project(name="真实搜索项目", description="搜索项目资料"))
    task = storage.add(Task(title="真实搜索任务", description="查找性能资料", tags=["搜索标签"], project_id=project.id))
    archived = storage.add(Task(title="已归档搜索任务", tags=["搜索标签"]))
    storage.archive(archived.id)
    monkeypatch.setattr("routes.search_routes.JSONStorage", lambda: storage)

    task_response = app.test_client().get("/search/?q=真实搜索任务")
    task_payload = task_response.get_json()
    assert task_response.status_code == 200
    assert task_payload["meta"] == {"query": "真实搜索任务", "count": 1}
    assert task_payload["data"][0]["kind"] == "task"
    assert task_payload["data"][0]["title"] == task.title
    assert task_payload["data"][0]["url"] == f"/task/{task.id}/edit"

    project_response = app.test_client().get("/search/?q=真实搜索项目")
    assert any(item["kind"] == "project" for item in project_response.get_json()["data"])

    tag_response = app.test_client().get("/search/?q=搜索标签")
    tag_payload = tag_response.get_json()
    assert any(item["kind"] == "tag" for item in tag_payload["data"])
    assert all(item["title"] != archived.title for item in tag_payload["data"])


def test_search_endpoint_empty_query_returns_recent_real_data(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    storage.add(Task(title="最近任务"))
    monkeypatch.setattr("routes.search_routes.JSONStorage", lambda: storage)

    response = app.test_client().get("/search/")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["meta"]["query"] == ""
    assert payload["data"][0]["title"] == "最近任务"
