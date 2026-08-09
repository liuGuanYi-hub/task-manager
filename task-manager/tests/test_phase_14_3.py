"""阶段 14.3：日历拖拽改期接口与页面契约。"""

from datetime import datetime

from models.task import Task
from storage.json_storage import JSONStorage
from web_app import app


def test_reschedule_endpoint_moves_date_and_preserves_time(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    task = storage.add(Task(title="拖拽改期任务", due_date=datetime(2026, 8, 4, 18, 30)))
    monkeypatch.setattr("routes.calendar_routes.JSONStorage", lambda: storage)

    response = app.test_client().post(
        f"/calendar/task/{task.id}/reschedule",
        json={"date": "2026-08-06"},
        headers={"Accept": "application/json"},
    )

    assert response.status_code == 200
    assert response.get_json()["data"]["due_date"] == "2026-08-06T18:30:00"
    assert storage.get_by_id(task.id).due_date == datetime(2026, 8, 6, 18, 30)


def test_reschedule_endpoint_rejects_invalid_date_without_mutation(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    task = storage.add(Task(title="日期校验任务", due_date=datetime(2026, 8, 4, 9, 0)))
    monkeypatch.setattr("routes.calendar_routes.JSONStorage", lambda: storage)

    response = app.test_client().post(
        f"/calendar/task/{task.id}/reschedule",
        json={"date": "not-a-date"},
        headers={"Accept": "application/json"},
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "invalid_date"
    assert storage.get_by_id(task.id).due_date == datetime(2026, 8, 4, 9, 0)


def test_calendar_views_expose_drop_targets_and_drag_script(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    storage.add(Task(title="日历拖拽入口", due_date=datetime(2026, 8, 4, 12, 0)))
    monkeypatch.setattr("routes.calendar_routes.JSONStorage", lambda: storage)
    client = app.test_client()

    month_body = client.get("/calendar/?date=2026-08-04").get_data(as_text=True)
    week_body = client.get("/calendar/week?date=2026-08-04").get_data(as_text=True)
    script = client.get("/static/calendar.js")

    assert 'src="/static/calendar.js"' in month_body
    assert 'src="/static/calendar.js"' in week_body
    assert 'data-calendar-drop-date="2026-08-04"' in month_body
    assert 'draggable="true"' in week_body
    assert script.status_code == 200
    assert "calendarRescheduleUrl" in script.get_data(as_text=True)
