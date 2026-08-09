"""阶段 16.4：SQLite 查询基线和 API 性能 smoke。"""

from time import perf_counter

from models.project import Project
from models.task import Status, Task
from storage.sqlite_storage import SQLiteStorage
from web_app import app


def _seed_sqlite_tasks(storage: SQLiteStorage, count: int = 120):
    project = storage.add_project(Project(name="性能 smoke 项目"))
    for index in range(count):
        storage.add(
            Task(
                title=f"性能 smoke 任务 {index + 1}",
                status=Status.IN_PROGRESS if index % 3 == 0 else Status.TODO,
                tags=["性能", "分页"] if index % 2 == 0 else ["分页"],
                project_id=project.id,
            )
        )
    return project


def test_sqlite_query_indexes_and_limit_offset_contract(tmp_path):
    storage = SQLiteStorage(tmp_path / "query-baseline.db")
    project = _seed_sqlite_tasks(storage)

    connection = storage._connect()
    try:
        index_names = {
            row["name"] for row in connection.execute("PRAGMA index_list(tasks)").fetchall()
        }
        tag_index_names = {
            row["name"] for row in connection.execute("PRAGMA index_list(task_tags)").fetchall()
        }
    finally:
        connection.close()

    tasks, total = storage.query_page(
        offset=20,
        limit=10,
        project_id=project.id,
        statuses=[Status.TODO.value, Status.IN_PROGRESS.value],
        tag="性能",
        sort_by="id",
    )

    assert "idx_tasks_project" in index_names
    assert "idx_tasks_status" in index_names
    assert "idx_tasks_archived" in index_names
    assert "idx_task_tags_tag_task" in tag_index_names
    assert total == 60
    assert len(tasks) == 10
    assert tasks[0].id < tasks[-1].id


def test_sqlite_api_pagination_performance_smoke(tmp_path, monkeypatch):
    storage = SQLiteStorage(tmp_path / "api-performance.db")
    project = _seed_sqlite_tasks(storage)
    monkeypatch.setattr("routes.api_routes.JSONStorage", lambda: storage)
    monkeypatch.delenv("TASK_MANAGER_API_TOKEN", raising=False)

    client = app.test_client()
    started = perf_counter()
    responses = [
        client.get(
            "/api/v1/tasks",
            query_string={
                "page": page,
                "page_size": 20,
                "project_id": project.id,
                "tag": "性能",
                "sort_by": "id",
            },
        )
        for page in range(1, 4)
    ]
    elapsed = perf_counter() - started

    assert all(response.status_code == 200 for response in responses)
    assert [response.get_json()["meta"]["total"] for response in responses] == [60, 60, 60]
    assert all(len(response.get_json()["data"]) == 20 for response in responses)
    # 120 条临时任务的三页 SQL 分页只设宽松上限，用于捕捉误回退到异常慢全量路径。
    assert elapsed < 5.0
    print(f"SQLite/API pagination smoke: {elapsed:.4f}s")
