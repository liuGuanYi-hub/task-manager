from datetime import datetime, timedelta

from models.project import Project
from models.task import Priority, Status, Task
from storage.json_storage import JSONStorage
from web_app import app


def _seed_editable_today_task(tmp_path):
    storage = JSONStorage(tmp_path / "tasks.json")
    project = storage.add_project(Project(name="抽屉编辑项目"))
    task = storage.add(
        Task(
            title="抽屉待编辑任务",
            description="旧描述",
            priority=Priority.MEDIUM,
            due_date=datetime.now() + timedelta(hours=2),
            tags=["旧标签"],
            project_id=project.id,
        )
    )
    return storage, project, task


def test_today_drawer_exposes_inline_edit_form(tmp_path, monkeypatch):
    storage, project, task = _seed_editable_today_task(tmp_path)
    monkeypatch.setattr("routes.today_routes.JSONStorage", lambda: storage)

    body = app.test_client().get("/today/").get_data(as_text=True)

    assert f'data-update-url="/task/{task.id}/update?next=/today/"' in body
    assert 'id="today-detail-form"' in body
    assert 'name="title"' in body
    assert 'name="description"' in body
    assert 'name="priority"' in body
    assert 'name="status"' in body
    assert 'name="due_date"' in body
    assert 'name="project_id"' in body
    assert 'name="tags"' in body
    assert "抽屉编辑项目" in body
    assert 'form="today-detail-form"' in body


def test_today_inline_edit_persists_and_returns_to_today(tmp_path, monkeypatch):
    storage, project, task = _seed_editable_today_task(tmp_path)
    monkeypatch.setattr("routes.today_routes.JSONStorage", lambda: storage)
    monkeypatch.setattr("web_app.storage", storage)

    response = app.test_client().post(
        f"/task/{task.id}/update?next=/today/",
        data={
            "title": "抽屉已保存任务",
            "description": "新的任务描述",
            "priority": "高",
            "status": "进行中",
            "due_date": "2026-08-12T09:30",
            "project_id": str(project.id),
            "tags": "新标签, 重点",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/today/")

    saved = storage.get_by_id(task.id)
    assert saved.title == "抽屉已保存任务"
    assert saved.description == "新的任务描述"
    assert saved.priority == Priority.HIGH
    assert saved.status == Status.IN_PROGRESS
    assert saved.due_date == datetime(2026, 8, 12, 9, 30)
    assert saved.project_id == project.id
    assert saved.tags == ["新标签", "重点"]


def test_task_update_rejects_external_next_redirect(tmp_path, monkeypatch):
    storage, project, task = _seed_editable_today_task(tmp_path)
    monkeypatch.setattr("web_app.storage", storage)

    response = app.test_client().post(
        f"/task/{task.id}/update?next=https://example.com/",
        data={
            "title": task.title,
            "description": task.description,
            "priority": task.priority.value,
            "status": task.status.value,
            "due_date": "",
            "project_id": str(project.id),
            "tags": "",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
