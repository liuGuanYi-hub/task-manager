"""阶段 10.1：Today 工作台 UI 预览页面测试。"""

from datetime import datetime

from models.task import Task
from storage.json_storage import JSONStorage
from web_app import app


def test_today_page_renders_ui_preview_sections_and_navigation(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    storage.add(Task(title="Today 测试任务", due_date=datetime.now()))
    monkeypatch.setattr("routes.today_routes.JSONStorage", lambda: storage)

    response = app.test_client().get("/today/")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Today 工作台" in body
    assert "实时工作台" in body
    assert "今天要做" in body
    assert "已逾期" in body
    assert "接下来" in body
    assert "还没有安排日期" in body
    assert 'href="/today/"' in body
    assert "当前展示未归档任务" in body
    assert 'id="today-detail-drawer"' in body
    assert "data-today-detail" in body
    assert 'src="/static/today.js"' in body


def test_today_page_exposes_real_navigation_routes():
    body = app.test_client().get("/today/").get_data(as_text=True)

    assert 'href="/board/"' in body
    assert 'href="/views/"' in body
    assert 'href="/calendar/"' in body


def test_today_drawer_script_is_available():
    response = app.test_client().get("/static/today.js")

    assert response.status_code == 200
    assert "today-drawer-layer" in response.get_data(as_text=True)
    assert "Escape" in response.get_data(as_text=True)
