"""阶段 11.6：统一动作撤销与错误回滚测试。"""

from datetime import datetime, timedelta

from models.task import Status, Task
from storage.json_storage import JSONStorage
from web_app import app


def test_task_action_returns_undo_payload_and_can_restore_completed_task(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    task = storage.add(Task(title="可撤销完成任务"))
    monkeypatch.setattr("routes.task_actions.JSONStorage", lambda: storage)
    client = app.test_client()

    completed = client.post(
        f"/task/{task.id}/action",
        json={"action": "complete", "next": "/today/"},
        headers={"Accept": "application/json"},
    )
    payload = completed.get_json()["data"]

    assert completed.status_code == 200
    assert payload["undo"]["snapshot"]["status"] == "待办"
    assert payload["undo"]["expected"]["status"] == "已完成"
    assert storage.get_by_id(task.id).status == Status.DONE

    undone = client.post(
        f"/task/{task.id}/action",
        json={
            "action": "undo",
            "next": "/today/",
            "snapshot": payload["undo"]["snapshot"],
            "expected": payload["undo"]["expected"],
        },
        headers={"Accept": "application/json"},
    )

    assert undone.status_code == 200
    assert undone.get_json()["data"]["action"] == "undo"
    assert storage.get_by_id(task.id).status == Status.TODO


def test_archived_task_can_be_undone_without_using_archive_schema(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    task = storage.add(Task(title="可撤销归档任务"))
    monkeypatch.setattr("routes.task_actions.JSONStorage", lambda: storage)
    client = app.test_client()

    archived = client.post(
        f"/task/{task.id}/action",
        json={"action": "archive", "next": "/"},
        headers={"Accept": "application/json"},
    )
    undo = archived.get_json()["data"]["undo"]

    assert archived.status_code == 200
    assert storage.get_by_id(task.id).archived is True

    restored = client.post(
        f"/task/{task.id}/action",
        json={"action": "undo", "snapshot": undo["snapshot"], "expected": undo["expected"]},
        headers={"Accept": "application/json"},
    )

    assert restored.status_code == 200
    assert storage.get_by_id(task.id).archived is False


def test_undo_rejects_a_task_changed_after_the_original_action(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    task = storage.add(Task(title="冲突保护任务"))
    monkeypatch.setattr("routes.task_actions.JSONStorage", lambda: storage)
    client = app.test_client()

    completed = client.post(
        f"/task/{task.id}/action",
        json={"action": "complete"},
        headers={"Accept": "application/json"},
    )
    undo = completed.get_json()["data"]["undo"]
    changed = storage.get_by_id(task.id)
    changed.title = "后来修改的标题"
    assert storage.update(changed) is True

    response = client.post(
        f"/task/{task.id}/action",
        json={"action": "undo", "snapshot": undo["snapshot"], "expected": undo["expected"]},
        headers={"Accept": "application/json"},
    )

    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == "undo_conflict"
    assert storage.get_by_id(task.id).title == "后来修改的标题"


def test_action_update_failure_restores_in_memory_task_state(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    task = storage.add(Task(title="失败回滚任务"))
    monkeypatch.setattr("routes.task_actions.JSONStorage", lambda: storage)
    monkeypatch.setattr(storage, "update", lambda current: False)

    response = app.test_client().post(
        f"/task/{task.id}/action",
        json={"action": "complete"},
        headers={"Accept": "application/json"},
    )

    assert response.status_code == 500
    assert response.get_json()["error"]["code"] == "update_failed"
    assert storage.get_by_id(task.id).status == Status.TODO


def test_agenda_renders_real_week_timeline_and_unplanned_queue(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    today_task = storage.add(
        Task(title="Agenda 今日任务", due_date=datetime.now().replace(hour=10, minute=0, second=0, microsecond=0))
    )
    tomorrow_task = storage.add(
        Task(title="Agenda 明日任务", due_date=datetime.now().replace(hour=15, minute=30, second=0, microsecond=0) + timedelta(days=1))
    )
    inbox_task = storage.add(Task(title="Agenda 未安排任务"))
    monkeypatch.setattr("web_app.storage", storage)
    monkeypatch.setattr("routes.agenda_routes.JSONStorage", lambda: storage)

    response = app.test_client().get("/agenda/")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "日程 Agenda" in body
    assert "EXECUTION WINDOW" in body
    assert today_task.title in body
    assert tomorrow_task.title in body
    assert inbox_task.title in body
    assert f'data-action-url="/task/{today_task.id}/action"' in body
    assert "未安排" in body
    assert 'src="/static/today.js"' in body
