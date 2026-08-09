from datetime import datetime, timedelta

from models.project import Project
from models.task import Status, Task
from storage.json_storage import JSONStorage
from web_app import app


def _seed_reminder_storage(tmp_path):
    storage = JSONStorage(tmp_path / "tasks.json")
    project = storage.add_project(Project(name="提醒项目"))
    now = datetime.now().replace(second=0, microsecond=0)
    overdue = storage.add(Task(title="提醒中心逾期", due_date=now - timedelta(days=1), project_id=project.id))
    due_soon = storage.add(Task(title="提醒中心即将到期", due_date=now + timedelta(days=1), project_id=project.id))
    done = storage.add(Task(title="已完成不提醒", status=Status.DONE, due_date=now + timedelta(hours=1)))
    archived = storage.add(Task(title="已归档不提醒", due_date=now + timedelta(hours=1)))
    storage.archive(archived.id)
    storage.add(Task(title="远期不提醒", due_date=now + timedelta(days=10)))
    storage.add(Task(title="无日期不提醒"))
    return storage, project, overdue, due_soon, done


def test_reminder_center_uses_active_due_date_rules(tmp_path, monkeypatch):
    storage, project, overdue, due_soon, done = _seed_reminder_storage(tmp_path)
    monkeypatch.setattr("routes.reminder_routes.JSONStorage", lambda: storage)

    response = app.test_client().get("/reminders/")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "提醒中心" in body
    assert "提醒中心逾期" in body
    assert "提醒中心即将到期" in body
    assert "已完成不提醒" not in body
    assert "已归档不提醒" not in body
    assert "远期不提醒" not in body
    assert "无日期不提醒" not in body
    assert "data-task-detail" in body
    assert f'data-update-url="/task/{overdue.id}/update?next=/reminders/"' in body
    assert f'data-task-id="{due_soon.id}"' in body
    assert project.id is not None
    assert done.id is not None


def test_reminder_completion_returns_to_center(tmp_path, monkeypatch):
    storage, _, overdue, *_ = _seed_reminder_storage(tmp_path)
    monkeypatch.setattr("routes.reminder_routes.JSONStorage", lambda: storage)
    monkeypatch.setattr("web_app.storage", storage)

    response = app.test_client().post(
        f"/task/{overdue.id}/toggle?next=/reminders/",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/reminders/")
    assert storage.get_by_id(overdue.id).status == Status.DONE
