from datetime import datetime, timedelta

from models.project import Project
from models.task import Priority, Status, Task
from storage.json_storage import JSONStorage
from web_app import app


def _seed_today_storage(tmp_path):
    storage = JSONStorage(tmp_path / "tasks.json")
    project = storage.add_project(Project(name="阶段 11 项目"))
    # 固定在当天中午，避免测试运行跨过午夜后“前一小时”落到前一天。
    current = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)

    today_task = storage.add(
        Task(
            title="真实今日任务",
            description="来自任务存储的描述",
            priority=Priority.HIGH,
            due_date=current + timedelta(hours=1),
            tags=["工作台"],
            project_id=project.id,
        )
    )
    done_today = storage.add(
        Task(
            title="今日已完成任务",
            status=Status.DONE,
            due_date=current - timedelta(hours=1),
        )
    )
    overdue_task = storage.add(
        Task(
            title="真实逾期任务",
            due_date=current - timedelta(days=2),
        )
    )
    completed_overdue = storage.add(
        Task(
            title="已完成的历史任务",
            status=Status.DONE,
            due_date=current - timedelta(days=3),
        )
    )
    upcoming_task = storage.add(
        Task(
            title="真实未来任务",
            due_date=current + timedelta(days=1),
        )
    )
    no_date_task = storage.add(Task(title="真实无日期任务"))
    archived_task = storage.add(Task(title="不应出现在 Today"))
    storage.archive(archived_task.id)

    return storage, today_task, done_today, overdue_task, completed_overdue, upcoming_task, no_date_task


def test_today_uses_real_tasks_and_exposes_detail_properties(tmp_path, monkeypatch):
    storage, today_task, _, _, completed_overdue, upcoming_task, no_date_task = _seed_today_storage(tmp_path)
    monkeypatch.setattr("routes.today_routes.JSONStorage", lambda: storage)

    response = app.test_client().get("/today/")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "实时工作台" in body
    assert "真实今日任务" in body
    assert "今日已完成任务" in body
    assert "真实逾期任务" in body
    assert "真实未来任务" in body
    assert "真实无日期任务" in body
    assert "不应出现在 Today" not in body
    assert "已完成的历史任务" not in body
    assert f'data-task-id="{today_task.id}"' in body
    assert f'data-edit-url="/task/{today_task.id}/edit"' in body
    assert "来自任务存储的描述" in body
    assert "阶段 11 项目" in body
    assert f'data-task-id="{upcoming_task.id}"' in body
    assert f'data-task-id="{no_date_task.id}"' in body
    assert completed_overdue.id is not None


def test_today_completion_form_persists_and_returns_to_today(tmp_path, monkeypatch):
    storage, today_task, *_ = _seed_today_storage(tmp_path)
    monkeypatch.setattr("routes.today_routes.JSONStorage", lambda: storage)
    monkeypatch.setattr("web_app.storage", storage)

    response = app.test_client().post(
        f"/task/{today_task.id}/toggle?next=/today/",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/today/")
    assert storage.get_by_id(today_task.id).status == Status.DONE
