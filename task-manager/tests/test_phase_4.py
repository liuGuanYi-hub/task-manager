"""阶段 4：保存筛选视图测试"""
from datetime import datetime, timedelta

from models.saved_view import SavedView
from models.task import Priority, Status, Task
from storage.json_storage import JSONStorage
from web_app import app


def test_query_saved_view_supports_combined_filters_and_due_range(tmp_path):
    storage = JSONStorage(tmp_path / "tasks.json")
    base_time = datetime(2026, 8, 3, 10, 0)
    matching = storage.add(
        Task(
            title="高优先级任务",
            priority=Priority.HIGH,
            status=Status.IN_PROGRESS,
            due_date=base_time + timedelta(days=2),
            tags=["本周"],
            created_at=base_time,
            updated_at=base_time,
        )
    )
    storage.add(
        Task(
            title="已完成任务",
            priority=Priority.HIGH,
            status=Status.DONE,
            due_date=base_time + timedelta(days=2),
            tags=["本周"],
        )
    )
    storage.add(
        Task(
            title="其他标签任务",
            priority=Priority.HIGH,
            status=Status.IN_PROGRESS,
            due_date=base_time + timedelta(days=10),
            tags=["以后"],
        )
    )
    view = SavedView(
        name="本周高优先级未完成",
        filters={
            "project_id": "all",
            "statuses": ["待办", "进行中"],
            "priority": "高",
            "tag": "本周",
            "due_start": "2026-08-01",
            "due_end": "2026-08-08",
            "sort_by": "updated_at",
            "reverse": True,
        },
    )

    results = storage.query_saved_view(view)

    assert [task.id for task in results] == [matching.id]


def test_saved_view_persists_and_deletes(tmp_path):
    path = tmp_path / "tasks.json"
    storage = JSONStorage(path)
    view = storage.add_saved_view(
        SavedView(name="高优先级未完成", filters={"priority": "高", "statuses": ["待办", "进行中"]})
    )

    reloaded = JSONStorage(path)
    saved = reloaded.get_saved_view_by_id(view.id)
    assert saved is not None
    assert saved.name == "高优先级未完成"
    assert saved.filters["statuses"] == ["待办", "进行中"]
    assert reloaded.delete_saved_view(view.id) is True
    assert reloaded.get_saved_views() == []


def test_views_page_filters_and_high_priority_preset(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    storage.add(Task(title="高优先级进行中", priority=Priority.HIGH, status=Status.IN_PROGRESS))
    storage.add(Task(title="低优先级待办", priority=Priority.LOW, status=Status.TODO))
    storage.add(Task(title="高优先级已完成", priority=Priority.HIGH, status=Status.DONE))
    monkeypatch.setattr("routes.views_routes.JSONStorage", lambda: storage)

    response = app.test_client().get("/views?preset=high-incomplete")

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "高优先级进行中" in body
    assert "低优先级待办" not in body
    assert "高优先级已完成" not in body


def test_views_can_save_read_and_delete_from_web(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    storage.add(Task(title="Web 视图任务", priority=Priority.HIGH, status=Status.TODO))
    monkeypatch.setattr("routes.views_routes.JSONStorage", lambda: storage)
    client = app.test_client()

    created = client.post(
        "/views/save",
        data={
            "name": "Web 高优先级",
            "project_id": "all",
            "statuses": ["待办"],
            "priority": "高",
            "sort_by": "created_at",
        },
    )

    assert created.status_code == 302
    view = storage.get_saved_views()[0]
    detail = client.get(f"/views/{view.id}")
    assert detail.status_code == 200
    assert "Web 视图任务" in detail.get_data(as_text=True)

    deleted = client.post(f"/views/{view.id}/delete")
    assert deleted.status_code == 302
    assert storage.get_saved_views() == []


def test_views_reject_invalid_filter_parameters(tmp_path, monkeypatch):
    monkeypatch.setattr("routes.views_routes.JSONStorage", lambda: JSONStorage(tmp_path / "tasks.json"))

    response = app.test_client().get("/views?sort_by=unknown")

    assert response.status_code == 400
