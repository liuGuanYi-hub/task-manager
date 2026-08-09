"""阶段 13.1：Today 专注计时 UI。"""

from web_app import app


def test_today_page_renders_focus_timer_without_new_task_fields():
    response = app.test_client().get("/today/")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'data-focus-timer' in body
    assert 'data-focus-storage-key="task-manager:focus-timer:v1"' in body
    assert 'data-focus-preset' in body
    assert 'src="/static/focus.js"' in body
    assert "parent_id" not in body
    assert "repeat_rule" not in body


def test_focus_timer_script_uses_local_state_and_accessible_controls():
    client = app.test_client()
    script = client.get("/static/focus.js")
    stylesheet = client.get("/static/app.css")

    assert script.status_code == 200
    script_body = script.get_data(as_text=True)
    assert "localStorage" in script_body
    assert "data-focus-start" in script_body
    assert "data-focus-preset" in script_body
    assert "visibilitychange" in script_body
    assert stylesheet.status_code == 200
    stylesheet_body = stylesheet.get_data(as_text=True)
    assert ".today-timer-card" in stylesheet_body
    assert ".today-timer-progress" in stylesheet_body
    assert "prefers-reduced-motion" in stylesheet_body
