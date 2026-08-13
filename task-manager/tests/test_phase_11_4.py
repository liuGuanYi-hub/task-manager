"""阶段 11.4：Inbox 与任务分流测试。"""

from datetime import date, datetime

from models.project import Project
from models.task import Status, Task
from storage.json_storage import JSONStorage
from web_app import app


def test_inbox_only_renders_active_unplanned_tasks(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    project = storage.add_project(Project(name="Inbox 项目"))
    unplanned = storage.add(Task(title="待整理任务"))
    scheduled = storage.add(Task(title="已安排任务", due_date=datetime.now()))
    archived = storage.add(Task(title="已归档任务", archived=True))
    monkeypatch.setattr("routes.inbox_routes.JSONStorage", lambda: storage)

    response = app.test_client().get("/inbox/")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert unplanned.title in body
    assert scheduled.title not in body
    assert archived.title not in body
    assert 'aria-current="page"' in body
    assert 'data-inbox-root' in body
    assert 'name="action" value="today"' in body
    assert 'name="action" value="date"' in body
    assert 'name="action" value="project"' in body
    assert str(project.id) in body


def test_inbox_schedule_to_today_updates_due_date_and_leaves_inbox(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    task = storage.add(Task(title="安排到今天"))
    monkeypatch.setattr("routes.inbox_routes.JSONStorage", lambda: storage)

    response = app.test_client().post(
        f"/inbox/task/{task.id}/schedule",
        data={"action": "today"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].startswith("/inbox/")
    assert storage.get_by_id(task.id).due_date.date() == date.today()
    assert "安排到今天" not in app.test_client().get("/inbox/").get_data(as_text=True)


def test_inbox_schedule_to_date_and_project_reuse_existing_fields(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    project = storage.add_project(Project(name="分流项目"))
    by_date = storage.add(Task(title="安排日期"))
    by_project = storage.add(Task(title="安排项目"))
    monkeypatch.setattr("routes.inbox_routes.JSONStorage", lambda: storage)
    client = app.test_client()

    date_response = client.post(
        f"/inbox/task/{by_date.id}/schedule",
        data={"action": "date", "due_date": "2026-08-20"},
        follow_redirects=False,
    )
    project_response = client.post(
        f"/inbox/task/{by_project.id}/schedule",
        data={"action": "project", "project_id": str(project.id)},
        follow_redirects=False,
    )

    assert date_response.status_code == 302
    assert storage.get_by_id(by_date.id).due_date == datetime(2026, 8, 20)
    assert project_response.status_code == 302
    assert storage.get_by_id(by_project.id).project_id == project.id
    assert storage.get_by_id(by_project.id).due_date is None


def test_inbox_quick_complete_and_archive_use_current_storage(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    toggle_task = storage.add(Task(title="快速完成"))
    archive_task = storage.add(Task(title="快速归档"))
    monkeypatch.setattr("routes.inbox_routes.JSONStorage", lambda: storage)
    client = app.test_client()

    toggle_response = client.post(f"/inbox/task/{toggle_task.id}/toggle")
    archive_response = client.post(f"/inbox/task/{archive_task.id}/archive")

    assert toggle_response.status_code == 302
    assert storage.get_by_id(toggle_task.id).status == Status.DONE
    assert archive_response.status_code == 302
    assert storage.get_by_id(archive_task.id).archived is True
