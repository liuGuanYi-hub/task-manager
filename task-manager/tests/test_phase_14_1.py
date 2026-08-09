from models.task import Status, Task
from storage.json_storage import JSONStorage
from web_app import app


def test_board_status_endpoint_supports_json_for_persistent_dragging(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    task = storage.add(Task(title="拖拽持久化任务", status=Status.TODO))
    monkeypatch.setattr("routes.board_routes.JSONStorage", lambda: storage)

    response = app.test_client().post(
        f"/board/task/{task.id}/status?project_id=all&response=json",
        data={"status": Status.IN_PROGRESS.value},
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "data": {
            "id": task.id,
            "status": Status.IN_PROGRESS.value,
            "project_id": None,
        }
    }
    saved = storage.get_by_id(task.id)
    assert saved.status == Status.IN_PROGRESS
    assert saved.completed_at is None


def test_board_status_endpoint_keeps_form_redirect_compatibility(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    task = storage.add(Task(title="表单状态任务", status=Status.TODO))
    monkeypatch.setattr("routes.board_routes.JSONStorage", lambda: storage)

    response = app.test_client().post(
        f"/board/task/{task.id}/status?project_id=all",
        data={"status": Status.DONE.value},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/board/?project_id=all")
    assert storage.get_by_id(task.id).status == Status.DONE
