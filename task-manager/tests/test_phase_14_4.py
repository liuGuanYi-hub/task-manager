"""阶段 14.4B/C：Agenda 筛选与拖拽改期契约测试。"""

from datetime import datetime, timedelta

from models.task import Task
from storage.json_storage import JSONStorage
from web_app import app


def _agenda_storage(tmp_path):
    storage = JSONStorage(tmp_path / "tasks.json")
    start = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
    today_tasks = [
        storage.add(Task(title=f"高密度任务 {index}", due_date=start + timedelta(minutes=index * 30)))
        for index in range(3)
    ]
    tomorrow = storage.add(Task(title="明日排期任务", due_date=start + timedelta(days=1)))
    unscheduled = storage.add(Task(title="Inbox 待安排事项"))
    return storage, today_tasks, tomorrow, unscheduled


def test_agenda_date_filter_limits_visible_day_groups(tmp_path, monkeypatch):
    storage, today_tasks, tomorrow, unscheduled = _agenda_storage(tmp_path)
    monkeypatch.setattr("routes.agenda_routes.JSONStorage", lambda: storage)
    client = app.test_client()
    today = datetime.now().date().isoformat()

    response = client.get(f"/agenda/?date={today}&date_filter=today")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'data-agenda-day="' + today + '"' in body
    assert today_tasks[0].title in body
    assert tomorrow.title not in body
    assert unscheduled.title not in body


def test_agenda_density_filter_keeps_only_busy_dates(tmp_path, monkeypatch):
    storage, today_tasks, tomorrow, _ = _agenda_storage(tmp_path)
    monkeypatch.setattr("routes.agenda_routes.JSONStorage", lambda: storage)
    client = app.test_client()
    today = datetime.now().date().isoformat()

    response = client.get(f"/agenda/?date={today}&density=busy")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'data-agenda-day="' + today + '"' in body
    assert today_tasks[2].title in body
    assert tomorrow.title not in body
    assert "高密度（3 项以上）" in body


def test_agenda_unscheduled_filter_shows_inbox_queue(tmp_path, monkeypatch):
    storage, _, tomorrow, unscheduled = _agenda_storage(tmp_path)
    monkeypatch.setattr("routes.agenda_routes.JSONStorage", lambda: storage)
    client = app.test_client()

    response = client.get("/agenda/?date_filter=unscheduled")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert unscheduled.title in body
    assert tomorrow.title not in body
    assert "未安排任务" in body


def test_agenda_task_exposes_reschedule_contract_and_calendar_endpoint_preserves_time(tmp_path, monkeypatch):
    storage, today_tasks, _, _ = _agenda_storage(tmp_path)
    monkeypatch.setattr("routes.agenda_routes.JSONStorage", lambda: storage)
    monkeypatch.setattr("routes.calendar_routes.JSONStorage", lambda: storage)
    client = app.test_client()
    today = datetime.now().date().isoformat()
    body = client.get(f"/agenda/?date={today}").get_data(as_text=True)

    task = today_tasks[0]
    assert f'data-agenda-reschedule-url="/calendar/task/{task.id}/reschedule"' in body
    assert 'draggable="true"' in body
    assert "键盘：聚焦任务后按 R" in body
    assert 'src="/static/agenda.js"' in body

    target_date = (datetime.now().date() + timedelta(days=4)).isoformat()
    response = client.post(
        f"/calendar/task/{task.id}/reschedule",
        json={"date": target_date},
        headers={"Accept": "application/json"},
    )

    assert response.status_code == 200
    assert storage.get_by_id(task.id).due_date.date().isoformat() == target_date
    assert storage.get_by_id(task.id).due_date.hour == 10


def test_agenda_client_contract_contains_touch_and_keyboard_recovery_paths():
    script = open("static/agenda.js", encoding="utf-8").read()

    assert "touchstart" in script
    assert "touchmove" in script
    assert "touchend" in script
    assert "event.key === \"ArrowLeft\"" in script
    assert "event.key === \"ArrowRight\"" in script
    assert "event.key === \"Enter\"" in script
    assert "event.key === \"Escape\"" in script
    assert "已取消触控改期" in script
    assert "任务仍在原日期" in script
