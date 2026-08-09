"""阶段 10.5：移动端与可访问性 UI 收尾测试。"""

from storage.json_storage import JSONStorage
from web_app import app


def test_base_page_renders_skip_link_mobile_navigation_and_current_page_state():
    response = app.test_client().get("/today/")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'class="skip-link" href="#main-content"' in body
    assert 'id="main-content"' in body
    assert 'class="mobile-bottom-nav"' in body
    assert 'aria-label="移动端快捷导航"' in body
    assert 'href="/today/"' in body
    assert 'aria-current="page"' in body


def test_views_page_renders_mobile_filter_drawer_controls(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    monkeypatch.setattr("routes.views_routes.JSONStorage", lambda: storage)

    response = app.test_client().get("/views/")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "data-mobile-filter-open" in body
    assert 'id="view-filter-panel"' in body
    assert "data-mobile-filter-close" in body
    assert 'src="/static/mobile-filters.js"' in body


def test_mobile_filter_script_and_accessibility_css_are_available():
    client = app.test_client()
    script = client.get("/static/mobile-filters.js")
    stylesheet = client.get("/static/app.css")

    assert script.status_code == 200
    assert "mobile-filter-open" in script.get_data(as_text=True)
    assert "Escape" in script.get_data(as_text=True)
    assert stylesheet.status_code == 200
    assert ".mobile-bottom-nav" in stylesheet.get_data(as_text=True)
    assert "prefers-reduced-motion" in stylesheet.get_data(as_text=True)
    assert ".skip-link" in stylesheet.get_data(as_text=True)
