"""阶段 10.3：WeKan 式看板 UI 交互预览测试。"""

from models.task import Status, Task
from storage.json_storage import JSONStorage
from web_app import app


def test_board_renders_drag_preview_and_accessible_column_controls(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    storage.add(Task(title="可拖拽任务", status=Status.TODO))
    monkeypatch.setattr("routes.board_routes.JSONStorage", lambda: storage)

    response = app.test_client().get("/board")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'data-board-root' in body
    assert 'data-board-card' in body
    assert 'draggable="true"' in body
    assert 'aria-grabbed="false"' in body
    assert 'data-board-dropzone' in body
    assert 'data-board-toggle' in body
    assert "拖拽后保存到任务状态" in body
    assert "data-board-status-url" in body
    assert 'src="/static/board.js"' in body


def test_board_interaction_script_is_available():
    response = app.test_client().get("/static/board.js")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "data-board-dropzone" in body
    assert "ArrowLeft" in body
    assert "is-drop-target" in body
    assert "保存失败，已恢复原状态" in body
    assert "fetch(statusUrl" in body
