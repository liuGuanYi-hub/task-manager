"""阶段 8：SQLite 条件查询和 LIMIT/OFFSET 分页测试。"""

from datetime import datetime, timedelta

from models.project import Project
from models.task import Priority, Status, Task
from storage.sqlite_storage import SQLiteStorage
from web_app import app


def test_sqlite_query_page_filters_exact_tags_and_counts(tmp_path):
    storage = SQLiteStorage(tmp_path / "query.db")
    project = storage.add_project(Project(name="查询项目"))
    other_project = storage.add_project(Project(name="其他项目"))
    base_time = datetime(2026, 8, 1, 9, 0)

    storage.add(
        Task(
            title="后端进行中",
            priority=Priority.HIGH,
            status=Status.IN_PROGRESS,
            tags=["后端", "接口"],
            project_id=project.id,
            due_date=base_time + timedelta(days=1),
        )
    )
    storage.add(
        Task(
            title="后端已完成",
            priority=Priority.HIGH,
            status=Status.DONE,
            tags=["后端"],
            project_id=project.id,
        )
    )
    archived = storage.add(
        Task(
            title="后端归档",
            priority=Priority.HIGH,
            tags=["后端"],
            project_id=project.id,
        )
    )
    storage.archive(archived.id)
    storage.add(Task(title="其他项目后端", tags=["后端"], project_id=other_project.id))

    tasks, total = storage.query_page(
        offset=0,
        limit=10,
        priority=Priority.HIGH.value,
        tag="后端",
        statuses=[Status.IN_PROGRESS.value],
        project_id=project.id,
        sort_by="id",
    )

    assert total == 1
    assert [task.title for task in tasks] == ["后端进行中"]

    archived_tasks, archived_total = storage.query_page(
        offset=0,
        limit=10,
        include_archived=True,
        tag="后端",
        project_id=project.id,
        sort_by="id",
    )
    assert archived_total == 3
    assert [task.title for task in archived_tasks] == ["后端进行中", "后端已完成", "后端归档"]


def test_api_uses_sqlite_query_page_instead_of_loading_all_tasks(tmp_path, monkeypatch):
    storage = SQLiteStorage(tmp_path / "api-query.db")
    for index in range(5):
        storage.add(Task(title=f"数据库分页 {index + 1}"))

    def fail_if_in_memory_query_is_used(*args, **kwargs):
        raise AssertionError("API 不应回退到 SQLite 的全量内存 query")

    monkeypatch.setattr(storage, "query", fail_if_in_memory_query_is_used)
    monkeypatch.setattr("routes.api_routes.JSONStorage", lambda: storage)

    response = app.test_client().get("/api/v1/tasks?page=2&page_size=2&sort_by=id")
    payload = response.get_json()

    assert response.status_code == 200
    assert [task["title"] for task in payload["data"]] == ["数据库分页 3", "数据库分页 4"]
    assert payload["meta"]["total"] == 5
    assert payload["meta"]["returned"] == 2


def test_sqlite_project_page_and_summary_use_database_aggregates(tmp_path):
    storage = SQLiteStorage(tmp_path / "projects.db")
    project = storage.add_project(Project(name="统计项目"))
    storage.add_project(Project(name="第二项目"))
    storage.add(Task(title="活动任务", project_id=project.id))
    storage.add(Task(title="完成任务", status=Status.DONE, project_id=project.id))
    archived = storage.add(Task(title="归档任务", project_id=project.id))
    storage.archive(archived.id)

    projects, total = storage.get_projects_page(offset=0, limit=1)
    summary = storage.get_project_summary(project.id)

    assert total == 2
    assert [item.name for item in projects] == ["统计项目"]
    assert summary == {"total_tasks": 2, "completed_tasks": 1}


def test_sqlite_rebuilds_tag_index_for_older_database_files(tmp_path):
    path = tmp_path / "legacy.db"
    storage = SQLiteStorage(path)
    storage.add(Task(title="旧标签任务", tags=["兼容标签"]))

    connection = storage._connect()
    try:
        connection.execute("DELETE FROM task_tags")
        connection.commit()
    finally:
        connection.close()

    reloaded = SQLiteStorage(path)
    tasks, total = reloaded.query_page(offset=0, limit=10, tag="兼容标签")

    assert total == 1
    assert [task.title for task in tasks] == ["旧标签任务"]
