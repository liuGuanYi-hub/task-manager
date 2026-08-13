"""阶段 10.6：信息架构与统一视图 Shell 契约测试。"""

from models.project import Project
from models.task import Task
from storage.json_storage import JSONStorage
from web_app import app


def test_base_page_renders_grouped_workspace_shell_and_quick_actions():
    response = app.test_client().get("/")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'class="nav-pills workspace-nav"' in body
    assert 'aria-label="工作区"' in body
    assert 'aria-label="规划"' in body
    assert 'aria-label="管理"' in body
    assert 'class="workspace-toolbar"' in body
    assert 'aria-label="工作区工具栏"' in body
    assert '搜索任务与项目' in body
    assert 'class="workspace-more"' in body
    assert 'class="mobile-bottom-nav-more"' in body


def test_project_detail_renders_unified_view_switcher(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    project = storage.add_project(Project(name="Shell 项目"))
    storage.add(Task(title="Shell 内任务", project_id=project.id))
    monkeypatch.setattr("routes.projects_routes.JSONStorage", lambda: storage)

    response = app.test_client().get(f"/projects/{project.id}")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'class="project-view-tabs"' in body
    assert 'aria-label="项目视图切换"' in body
    assert ">概览</a>" in body
    assert f"/views/?project_id={project.id}" in body
    assert f"/board/?project_id={project.id}" in body
    assert "项目工作区" in body


def test_shell_stylesheet_contains_desktop_and_mobile_layout_contract():
    response = app.test_client().get("/static/app.css")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert ".workspace-nav" in body
    assert ".workspace-toolbar" in body
    assert ".project-view-tabs" in body
    assert ".mobile-bottom-nav-more" in body
    assert ".task-info" in body and "flex: 1 1 auto" in body
    assert ".task-actions" in body and "flex: 0 0 auto" in body
    assert "@media (max-width: 760px)" in body
