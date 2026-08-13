"""阶段 11.5：统一任务操作层测试。"""

from datetime import date, datetime, timedelta

from models.project import Project
from models.task import Status, Task
from storage.json_storage import JSONStorage
from web_app import app


def test_unified_task_action_completes_and_returns_json(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    task = storage.add(Task(title="统一完成任务"))
    monkeypatch.setattr("routes.task_actions.JSONStorage", lambda: storage)

    response = app.test_client().post(
        f"/task/{task.id}/action",
        json={"action": "complete", "next": "/today/"},
        headers={"Accept": "application/json"},
    )

    assert response.status_code == 200
    assert response.get_json()["data"]["action"] == "complete"
    assert response.get_json()["data"]["next"] == "/today/"
    assert response.get_json()["data"]["task"]["status"] == "已完成"
    assert storage.get_by_id(task.id).status == Status.DONE


def test_unified_task_action_delays_and_archives_with_html_redirect(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    delayed = storage.add(Task(title="统一延后任务"))
    archived = storage.add(Task(title="统一归档任务"))
    monkeypatch.setattr("routes.task_actions.JSONStorage", lambda: storage)
    client = app.test_client()

    delayed_response = client.post(
        f"/task/{delayed.id}/action",
        data={"action": "delay", "next": "/reminders/"},
        follow_redirects=False,
    )
    archive_response = client.post(
        f"/task/{archived.id}/action",
        data={"action": "archive", "next": "/"},
        follow_redirects=False,
    )

    assert delayed_response.status_code == 302
    assert delayed_response.headers["Location"] == "/reminders/"
    assert storage.get_by_id(delayed.id).due_date.date() == date.today() + timedelta(days=1)
    assert archive_response.status_code == 302
    assert storage.get_by_id(archived.id).archived is True


def test_unified_task_action_rejects_invalid_action_and_bad_date(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    task = storage.add(Task(title="统一动作校验"))
    monkeypatch.setattr("routes.task_actions.JSONStorage", lambda: storage)
    client = app.test_client()

    invalid_action = client.post(
        f"/task/{task.id}/action",
        json={"action": "unknown"},
        headers={"Accept": "application/json"},
    )
    invalid_date = client.post(
        f"/task/{task.id}/action",
        data={"action": "delay", "due_date": "not-a-date"},
        headers={"Accept": "application/json"},
    )

    assert invalid_action.status_code == 400
    assert invalid_action.get_json()["error"]["code"] == "invalid_action"
    assert invalid_date.status_code == 400
    assert invalid_date.get_json()["error"]["code"] == "invalid_due_date"


def test_main_task_pages_share_action_url_and_drawer_controls(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    project = storage.add_project(Project(name="统一操作项目"))
    due_task = storage.add(
        Task(
            title="共享详情任务",
            due_date=datetime.now().replace(second=0, microsecond=0),
            project_id=project.id,
        )
    )
    inbox_task = storage.add(Task(title="共享 Inbox 任务"))
    monkeypatch.setattr("web_app.storage", storage)
    for module in (
        "routes.today_routes",
        "routes.board_routes",
        "routes.calendar_routes",
        "routes.reminder_routes",
        "routes.inbox_routes",
    ):
        monkeypatch.setattr(f"{module}.JSONStorage", lambda storage=storage: storage)

    client = app.test_client()
    pages = [
        "/",
        "/today/",
        "/board/",
        "/calendar/",
        "/calendar/week",
        "/reminders/",
        "/inbox/",
    ]
    bodies = {page: client.get(page).get_data(as_text=True) for page in pages}

    for page, body in bodies.items():
        if page == "/calendar/":
            assert f'"action_url": "/task/{due_task.id}/action"' in body
        elif page == "/inbox/":
            assert f'data-action-url="/task/{inbox_task.id}/action"' in body
        else:
            assert f'data-action-url="/task/{due_task.id}/action"' in body
        assert 'data-task-action="complete"' in body
        assert 'data-task-action="delay"' in body
        assert 'data-task-action="archive"' in body
        assert 'src="/static/today.js"' in body

    assert f"data-action-url=\"/task/{inbox_task.id}/action\"" in bodies["/inbox/"]
