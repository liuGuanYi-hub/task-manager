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
    assert f'data-agenda-quick-date="{datetime.now().date().isoformat()}"' in body
    assert f'data-agenda-quick-date="{(datetime.now().date() + timedelta(days=1)).isoformat()}"' in body
    assert "下周一" in body
    assert "快速安排" in body
    assert f'data-agenda-action-url="/task/{unscheduled.id}/action"' in body


def test_agenda_period_filter_groups_tasks_by_due_time(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    today = datetime.now().date()
    period_tasks = [
        storage.add(Task(title="Agenda 深夜任务", due_date=datetime.combine(today, datetime.min.time()).replace(hour=2))),
        storage.add(Task(title="Agenda 上午任务", due_date=datetime.combine(today, datetime.min.time()).replace(hour=9))),
        storage.add(Task(title="Agenda 下午任务", due_date=datetime.combine(today, datetime.min.time()).replace(hour=14))),
        storage.add(Task(title="Agenda 晚上任务", due_date=datetime.combine(today, datetime.min.time()).replace(hour=20))),
    ]
    monkeypatch.setattr("routes.agenda_routes.JSONStorage", lambda: storage)
    client = app.test_client()

    response = client.get(f"/agenda/?date={today.isoformat()}&date_filter=today&period=morning")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert period_tasks[1].title in body
    assert period_tasks[0].title not in body
    assert period_tasks[2].title not in body
    assert period_tasks[3].title not in body
    assert "上午 · 06:00–12:00" in body
    assert 'data-agenda-drop-period="morning"' in body
    assert 'data-agenda-count>1 项任务<' in body


def test_agenda_quick_schedule_action_assigns_default_morning_slot(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    task = storage.add(Task(title="Agenda 快捷安排任务"))
    monkeypatch.setattr("routes.task_actions.JSONStorage", lambda: storage)
    client = app.test_client()
    target_date = (datetime.now().date() + timedelta(days=1)).isoformat()

    response = client.post(
        f"/task/{task.id}/action",
        data={"action": "delay", "due_date": target_date + "T09:00", "next": "/agenda/"},
        headers={"Accept": "application/json"},
    )

    assert response.status_code == 200
    assert response.get_json()["data"]["message"] == "任务已改期"
    assert storage.get_by_id(task.id).due_date.isoformat() == target_date + "T09:00:00"


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
    assert "data-agenda-quick-date" in script
    assert "handleQuickSchedule" in script
    assert "due_date" in script
    assert "findKeyboardTargetZone" in script
    assert "已取消触控改期" in script
    assert "任务仍在原日期" in script
