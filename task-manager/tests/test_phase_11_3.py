from datetime import datetime
import json

from models.project import Project
from models.task import Priority, Status, Task
from storage.json_storage import JSONStorage
from web_app import app


def _seed_board_calendar_storage(tmp_path):
    storage = JSONStorage(tmp_path / "tasks.json")
    project = storage.add_project(Project(name="统一详情项目"))
    task = storage.add(
        Task(
            title="看板日历共用任务",
            description="来自统一详情抽屉的任务",
            priority=Priority.HIGH,
            status=Status.IN_PROGRESS,
            due_date=datetime.now().replace(second=0, microsecond=0),
            tags=["统一入口"],
            project_id=project.id,
        )
    )
    return storage, project, task


def test_board_reuses_today_detail_drawer_and_edit_data(tmp_path, monkeypatch):
    storage, project, task = _seed_board_calendar_storage(tmp_path)
    monkeypatch.setattr("routes.board_routes.JSONStorage", lambda: storage)

    response = app.test_client().get("/board/")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert f'data-task-id="{task.id}"' in body
    assert "data-task-detail" in body
    assert "统一详情项目" in body
    assert task.title in body
    assert 'id="today-detail-form"' in body
    assert 'src="/static/today.js"' in body
    assert f'data-update-url="/task/{task.id}/update?' in body
    assert project.id is not None


def test_calendar_serializes_detail_data_and_reuses_drawer(tmp_path, monkeypatch):
    storage, _, task = _seed_board_calendar_storage(tmp_path)
    monkeypatch.setattr("routes.calendar_routes.JSONStorage", lambda: storage)

    response = app.test_client().get("/calendar/")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert f'"id": {task.id}' in body
    assert json.dumps(task.description, ensure_ascii=True) in body
    assert "data-task-detail" in body
    assert "taskDetailAttrs" in body
    assert 'id="today-detail-form"' in body
    assert 'src="/static/today.js"' in body
    assert f"/task/{task.id}/update?next=/calendar/" in body
