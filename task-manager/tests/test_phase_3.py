"""阶段 3：WeKan 式三列看板和状态流转测试"""
from models.project import Project
from models.task import Status, Task
from routes.board_routes import ANY_PROJECT, parse_project_filter
from storage.json_storage import JSONStorage
from web_app import app


def test_parse_board_project_filter():
    assert parse_project_filter(None) is ANY_PROJECT
    assert parse_project_filter("all") is ANY_PROJECT
    assert parse_project_filter("none") is None
    assert parse_project_filter("7") == 7


def test_board_renders_three_status_columns_and_cards(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    storage.add(Task(title="待办卡片", status=Status.TODO))
    storage.add(Task(title="进行中卡片", status=Status.IN_PROGRESS))
    storage.add(Task(title="完成卡片", status=Status.DONE))
    storage.add(Task(title="隐藏归档卡片", archived=True))
    monkeypatch.setattr("routes.board_routes.JSONStorage", lambda: storage)

    response = app.test_client().get("/board")

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "任务看板" in body
    assert "待办卡片" in body
    assert "进行中卡片" in body
    assert "完成卡片" in body
    assert "隐藏归档卡片" not in body
    assert body.count("board-column") >= 3


def test_board_project_filter_keeps_other_projects_out(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    project_a = storage.add_project(Project(name="项目 A"))
    project_b = storage.add_project(Project(name="项目 B"))
    storage.add(Task(title="A 的卡片", project_id=project_a.id))
    storage.add(Task(title="B 的卡片", project_id=project_b.id))
    storage.add(Task(title="未归属卡片"))
    monkeypatch.setattr("routes.board_routes.JSONStorage", lambda: storage)

    response = app.test_client().get(f"/board?project_id={project_a.id}")

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "A 的卡片" in body
    assert "B 的卡片" not in body
    assert "未归属卡片" not in body
    assert "项目 A" in body


def test_board_can_move_task_and_persist_completion_time(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    task = storage.add(Task(title="待移动任务"))
    monkeypatch.setattr("routes.board_routes.JSONStorage", lambda: storage)

    response = app.test_client().post(
        f"/board/task/{task.id}/status?project_id=all",
        data={"status": "已完成"},
    )

    assert response.status_code == 302
    saved = storage.get_by_id(task.id)
    assert saved.status == Status.DONE
    assert saved.completed_at is not None
    assert saved.updated_at == saved.completed_at


def test_board_rejects_invalid_status_and_wrong_project(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    project = storage.add_project(Project(name="限制项目"))
    task = storage.add(Task(title="项目任务", project_id=project.id))
    monkeypatch.setattr("routes.board_routes.JSONStorage", lambda: storage)

    invalid = app.test_client().post(
        f"/board/task/{task.id}/status?project_id={project.id}",
        data={"status": "不存在"},
    )
    wrong_project = app.test_client().post(
        f"/board/task/{task.id}/status?project_id=none",
        data={"status": "进行中"},
    )

    assert invalid.status_code == 400
    assert wrong_project.status_code == 404
