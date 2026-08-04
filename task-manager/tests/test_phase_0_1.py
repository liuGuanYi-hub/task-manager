"""阶段 0/1：日期语义、提醒过滤和归档兼容测试"""
from datetime import date, datetime, timedelta

from click.testing import CliRunner

from commands.create import create_task
from models.task import Priority, Status, Task, parse_datetime
from routes.calendar_routes import get_tasks_for_date
from storage.json_storage import JSONStorage
from utils.helpers import check_due_tasks, check_overdue_tasks
from web_app import app


def test_legacy_json_gets_defaults_for_new_fields():
    """旧 JSON 缺少阶段 1 字段时仍然可以读取。"""
    task = Task.from_dict(
        {
            "id": 1,
            "title": "旧数据",
            "description": "兼容测试",
            "priority": "中",
            "status": "待办",
            "created_at": "2026-08-01T10:00:00",
            "due_date": None,
            "tags": [],
        }
    )

    assert task.updated_at == task.created_at
    assert task.completed_at is None
    assert task.archived is False


def test_parse_datetime_normalizes_zulu_timezone():
    parsed = parse_datetime("2026-08-04T00:00:00Z")

    assert parsed is not None
    assert parsed.tzinfo is None


def test_storage_update_tracks_completion_time(tmp_path):
    storage = JSONStorage(tmp_path / "tasks.json")
    task = storage.add(Task(title="完成时间测试"))
    original_updated_at = task.updated_at

    task.status = Status.DONE
    assert storage.update(task) is True

    saved = JSONStorage(tmp_path / "tasks.json").get_by_id(task.id)
    assert saved is not None
    assert saved.completed_at is not None
    assert saved.updated_at >= original_updated_at

    saved.status = Status.TODO
    assert storage.update(saved) is True
    assert storage.get_by_id(task.id).completed_at is None


def test_archive_hides_task_but_restore_keeps_data(tmp_path):
    storage = JSONStorage(tmp_path / "tasks.json")
    task = storage.add(Task(title="归档测试"))

    assert storage.archive(task.id) is True
    assert storage.get_all() == []
    assert storage.get_archived()[0].title == "归档测试"
    assert storage.get_all(include_archived=True)[0].archived is True

    assert storage.restore(task.id) is True
    assert storage.get_all()[0].title == "归档测试"
    assert storage.get_all()[0].archived is False


def test_storage_query_centralizes_filters_and_sorting(tmp_path):
    storage = JSONStorage(tmp_path / "tasks.json")
    storage.add(Task(title="低优先级", priority=Priority.LOW))
    storage.add(Task(title="高优先级", priority=Priority.HIGH, tags=["工作"]))

    results = storage.query(priority="高", tag="工作", sort_by="title")

    assert [task.title for task in results] == ["高优先级"]


def test_reminders_ignore_done_and_archived_tasks():
    now = datetime.now()
    due_soon = Task(title="即将到期", due_date=now + timedelta(hours=1))
    done = Task(title="已完成", status=Status.DONE, due_date=now + timedelta(hours=1))
    archived = Task(title="已归档", due_date=now + timedelta(hours=1), archived=True)
    overdue = Task(title="已过期", due_date=now - timedelta(hours=1))

    due_tasks = check_due_tasks([due_soon, done, archived], days=1)
    overdue_tasks = check_overdue_tasks([overdue, done, archived])

    assert [task.title for task in due_tasks] == ["即将到期"]
    assert [task.title for task in overdue_tasks] == ["已过期"]


def test_calendar_uses_due_date_instead_of_created_date():
    task = Task(
        title="截止日期任务",
        created_at=datetime(2026, 8, 1, 10, 0),
        due_date=datetime(2026, 8, 4, 18, 0),
    )

    assert get_tasks_for_date([task], date(2026, 8, 4)) == [task]
    assert get_tasks_for_date([task], date(2026, 8, 1)) == []


def test_create_command_accepts_due_date(tmp_path, monkeypatch):
    storage_path = tmp_path / "tasks.json"
    monkeypatch.setattr(
        "commands.create.JSONStorage",
        lambda: JSONStorage(storage_path),
    )

    result = CliRunner().invoke(
        create_task,
        ["命令行截止时间", "--due-date", "2026-08-08 18:00"],
    )

    assert result.exit_code == 0
    saved = JSONStorage(storage_path).get_all()[0]
    assert saved.due_date == datetime(2026, 8, 8, 18, 0)


def test_web_create_accepts_due_date(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    monkeypatch.setattr("web_app.storage", storage)

    response = app.test_client().post(
        "/new",
        data={
            "title": "Web 截止时间",
            "description": "表单测试",
            "priority": "中",
            "due_date": "2026-08-08T18:00",
            "tags": "测试",
        },
    )

    assert response.status_code == 302
    assert storage.get_all()[0].due_date == datetime(2026, 8, 8, 18, 0)
