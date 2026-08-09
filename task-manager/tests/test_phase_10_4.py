"""阶段 10.4：搜索与快捷操作 UI 预览测试。"""

from web_app import app


def test_base_page_renders_global_search_palette_preview():
    response = app.test_client().get("/")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "data-search-open" in body
    assert 'id="global-search-panel"' in body
    assert 'id="global-search-input"' in body
    assert "data-search-results" in body
    assert "data-search-empty" in body
    assert "搜索当前任务、项目和标签" in body
    assert "data-search-endpoint" in body
    assert 'data-search-command="n"' in body
    assert 'src="/static/search.js"' in body


def test_search_script_is_available_and_scopes_preview_filtering():
    response = app.test_client().get("/static/search.js")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "filterResults" in body
    assert "loadResults" in body
    assert "createResultItem" in body
    assert "isTypingTarget" in body
    assert "runCommandShortcut" in body
    assert "Escape" in body
    assert "data-search-empty" in body
