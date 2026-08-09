"""阶段 13.2：Today 快速收集与本地专注任务绑定。"""

from datetime import date, datetime

from models.task import Task
from storage.json_storage import JSONStorage
from web_app import app


def test_today_exposes_quick_capture_and_focus_task_controls(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    storage.add(Task(title="准备发布", due_date=datetime.combine(date.today(), datetime.min.time())))
    monkeypatch.setattr("routes.today_routes.JSONStorage", lambda: storage)

    response = app.test_client().get("/today/")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'action="/new?next=/today/"' in body
    assert 'data-quick-capture-input' in body
    assert 'data-focus-task-select' in body
    assert 'data-focus-task-label' in body
    assert 'data-focus-task-clear' in body


def test_quick_capture_creates_task_and_returns_to_today(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    monkeypatch.setattr("web_app.storage", storage)

    response = app.test_client().post(
        "/new?next=/today/",
        data={"title": "快速收集的下一步", "priority": "中"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/today/")
    assert storage.get_all()[0].title == "快速收集的下一步"


def test_quick_capture_rejects_external_next_redirect(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    monkeypatch.setattr("web_app.storage", storage)

    response = app.test_client().post(
        "/new?next=//example.invalid/redirect",
        data={"title": "仍然回到首页", "priority": "中"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


def test_focus_script_keeps_task_binding_local_and_handles_keyboard_capture():
    client = app.test_client()
    script = client.get("/static/focus.js").get_data(as_text=True)
    today_script = client.get("/static/today.js").get_data(as_text=True)
    stylesheet = client.get("/static/app.css").get_data(as_text=True)

    assert "focusTask" in script
    assert "localStorage" in script
    assert "data-focus-task-select" in script
    assert "data-focus-task-clear" in script
    assert "data-quick-capture-input" in today_script
    assert ".today-focus-task" in stylesheet
    assert ".today-quick-add-form" in stylesheet
