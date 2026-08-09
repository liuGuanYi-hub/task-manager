"""阶段 15.1：任务列表批量操作。"""

from models.task import Status, Task
from storage.json_storage import JSONStorage
from web_app import app


def test_task_list_exposes_bulk_selection_toolbar(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    task = storage.add(Task(title="批量选择任务"))
    monkeypatch.setattr("web_app.storage", storage)

    response = app.test_client().get("/")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'id="bulk-task-form"' in body
    assert 'action="/tasks/bulk"' in body
    assert 'data-bulk-select-all' in body
    assert f'value="{task.id}"' in body
    assert 'src="/static/bulk.js"' in body


def test_bulk_complete_updates_selected_tasks_and_reports_count(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    first = storage.add(Task(title="批量完成一"))
    second = storage.add(Task(title="批量完成二", status=Status.IN_PROGRESS))
    monkeypatch.setattr("web_app.storage", storage)

    response = app.test_client().post(
        "/tasks/bulk",
        data={
            "task_ids": [str(first.id), str(second.id)],
            "action": "complete",
            "next": "/",
        },
    )

    assert response.status_code == 302
    assert "bulk_action=complete" in response.headers["Location"]
    assert storage.get_by_id(first.id).status == Status.DONE
    assert storage.get_by_id(second.id).status == Status.DONE
    feedback = app.test_client().get(response.headers["Location"])
    assert "已批量完成 2 个任务" in feedback.get_data(as_text=True)


def test_bulk_archive_supports_json_and_hides_tasks(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    task = storage.add(Task(title="批量归档任务"))
    monkeypatch.setattr("web_app.storage", storage)

    response = app.test_client().post(
        "/tasks/bulk",
        json={"task_ids": [task.id], "action": "archive"},
        headers={"Accept": "application/json"},
    )

    assert response.status_code == 200
    assert response.get_json()["data"] == {"action": "archive", "updated": 1}
    assert storage.get_all() == []
    assert storage.get_archived()[0].title == "批量归档任务"


def test_bulk_rejects_empty_selection(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    monkeypatch.setattr("web_app.storage", storage)

    response = app.test_client().post(
        "/tasks/bulk",
        json={"task_ids": [], "action": "complete"},
        headers={"Accept": "application/json"},
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "empty_selection"
