"""阶段 14.2：日历周视图与截止日期分组。"""

from datetime import datetime

from models.task import Task
from storage.json_storage import JSONStorage
from web_app import app


def test_calendar_week_groups_due_tasks_and_reuses_detail_drawer(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    current_week_task = storage.add(
        Task(title="周内截止任务", due_date=datetime(2026, 8, 4, 18, 0))
    )
    archived_task = storage.add(
        Task(title="不应显示的归档任务", due_date=datetime(2026, 8, 5, 18, 0), archived=True)
    )
    outside_week_task = storage.add(
        Task(title="下一周任务", due_date=datetime(2026, 8, 12, 18, 0))
    )
    monkeypatch.setattr("routes.calendar_routes.JSONStorage", lambda: storage)

    response = app.test_client().get("/calendar/week?date=2026-08-05")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "日历周视图" in body
    assert "calendar-week-grid" in body
    assert current_week_task.title in body
    assert f'data-task-id="{current_week_task.id}"' in body
    assert "不应显示的归档任务" not in body
    assert outside_week_task.title not in body
    assert 'id="today-detail-form"' in body
    assert 'src="/static/today.js"' in body


def test_calendar_month_view_links_to_real_week_view():
    response = app.test_client().get("/calendar/")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'href="/calendar/week"' in body
