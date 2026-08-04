"""阶段 9：主题模式和深色模式页面渲染测试。"""

from storage.json_storage import JSONStorage
from web_app import app


def test_settings_renders_theme_mode_and_accent_controls(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "routes.settings_routes.JSONStorage",
        lambda: JSONStorage(tmp_path / "tasks.json"),
    )

    response = app.test_client().get("/settings/")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'data-theme-mode="system"' in body
    assert 'data-theme-mode="light"' in body
    assert 'data-theme-mode="dark"' in body
    assert 'data-accent="default"' in body
    assert 'data-accent="mint"' in body


def test_base_page_loads_theme_script_and_theme_css():
    client = app.test_client()

    page = client.get("/")
    script = client.get("/static/theme.js")
    stylesheet = client.get("/static/app.css")

    assert page.status_code == 200
    assert 'src="/static/theme.js"' in page.get_data(as_text=True)
    assert script.status_code == 200
    assert "task-manager-theme-mode" in script.get_data(as_text=True)
    assert stylesheet.status_code == 200
    assert 'html[data-theme="dark"]' in stylesheet.get_data(as_text=True)
    assert 'prefers-color-scheme: dark' in stylesheet.get_data(as_text=True)
