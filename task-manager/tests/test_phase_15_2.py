"""阶段 15.2：批量修改优先级、项目和标签。"""

from models.project import Project
from models.task import Priority, Task
from storage.json_storage import JSONStorage
from web_app import app


def test_bulk_toolbar_exposes_property_edit_controls(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    project = storage.add_project(Project(name="批量项目"))
    storage.add(Task(title="批量属性任务", project_id=project.id))
    monkeypatch.setattr("web_app.storage", storage)

    body = app.test_client().get("/").get_data(as_text=True)

    assert 'data-bulk-value="priority"' in body
    assert 'data-bulk-value="project"' in body
    assert 'data-bulk-value="tags"' in body
    assert "批量项目" in body
    assert "应用优先级" in body
    assert "应用项目" in body
    assert "应用标签" in body


def test_bulk_property_actions_update_selected_tasks(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    project = storage.add_project(Project(name="批量更新项目"))
    first = storage.add(Task(title="属性任务一"))
    second = storage.add(Task(title="属性任务二"))
    monkeypatch.setattr("web_app.storage", storage)
    client = app.test_client()

    priority_response = client.post(
        "/tasks/bulk",
        data={
            "task_ids": [str(first.id), str(second.id)],
            "action": "priority",
            "priority": "高",
            "next": "/",
        },
    )
    project_response = client.post(
        "/tasks/bulk",
        data={
            "task_ids": [str(first.id), str(second.id)],
            "action": "project",
            "project_id": str(project.id),
            "next": "/",
        },
    )
    tags_response = client.post(
        "/tasks/bulk",
        json={"task_ids": [first.id, second.id], "action": "tags", "tags": ["工作", "重点"]},
        headers={"Accept": "application/json"},
    )

    assert priority_response.status_code == 302
    assert project_response.status_code == 302
    assert tags_response.status_code == 200
    assert tags_response.get_json()["data"] == {"action": "tags", "updated": 2}
    assert storage.get_by_id(first.id).priority == Priority.HIGH
    assert storage.get_by_id(second.id).priority == Priority.HIGH
    assert storage.get_by_id(first.id).project_id == project.id
    assert storage.get_by_id(second.id).project_id == project.id
    assert storage.get_by_id(first.id).tags == ["工作", "重点"]
    assert storage.get_by_id(second.id).tags == ["工作", "重点"]


def test_bulk_project_rejects_unknown_project_without_mutation(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    task = storage.add(Task(title="项目校验任务"))
    monkeypatch.setattr("web_app.storage", storage)

    response = app.test_client().post(
        "/tasks/bulk",
        json={"task_ids": [task.id], "action": "project", "project_id": 9999},
        headers={"Accept": "application/json"},
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "invalid_project"
    assert storage.get_by_id(task.id).project_id is None
