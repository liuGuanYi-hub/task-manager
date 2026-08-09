"""阶段 16.6：发布文档和 UI 资源可用性检查。"""

from pathlib import Path

from web_app import app


APP_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = APP_ROOT.parent


def test_release_pages_render_shared_shell_and_static_assets():
    client = app.test_client()
    pages = ["/", "/today/", "/reminders/", "/board/", "/calendar/", "/views/", "/settings/"]

    for path in pages:
        response = client.get(path)
        body = response.get_data(as_text=True)

        assert response.status_code == 200, path
        assert 'href="/static/app.css"' in body, path
        assert 'id="global-search-panel"' in body, path


def test_release_static_scripts_are_reachable():
    client = app.test_client()
    assets = [
        "/static/theme.js",
        "/static/search.js",
        "/static/today.js",
        "/static/board.js",
        "/static/mobile-filters.js",
    ]

    for asset in assets:
        response = client.get(asset)
        assert response.status_code == 200, asset
        assert response.data, asset


def test_release_docs_match_current_branch_and_security_workflow():
    root_readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    app_readme = (APP_ROOT / "README.md").read_text(encoding="utf-8")
    deploy_doc = (APP_ROOT / "DEPLOY.md").read_text(encoding="utf-8")

    assert "security_scan.py" in root_readme
    assert "task-manager/docs/API.md" in root_readme
    assert "docs/API.md" in app_readme
    assert "git push origin master" in deploy_doc
    assert "git push https://<your-username>:<your-token>@" not in deploy_doc
    assert "YOUR_API_TOKEN" in deploy_doc
