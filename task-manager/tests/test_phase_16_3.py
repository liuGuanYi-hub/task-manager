"""阶段 16.3：API 发现入口和发布 smoke。"""

from web_app import app


def test_api_index_exposes_version_auth_and_pagination_contract(monkeypatch):
    monkeypatch.setenv("TASK_MANAGER_API_TOKEN", "test-only-token")

    response = app.test_client().get("/api/v1")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["data"]["version"] == "v1"
    assert payload["data"]["base_path"] == "/api/v1"
    assert payload["data"]["authentication"]["type"] == "bearer"
    assert payload["data"]["pagination"]["max_page_size"] == 100
    assert "/api/v1/tasks" in {item["path"] for item in payload["data"]["endpoints"]}


def test_public_api_discovery_and_health_remain_available_with_auth_enabled(monkeypatch):
    monkeypatch.setenv("TASK_MANAGER_API_TOKEN", "test-only-token")
    client = app.test_client()

    discovery = client.get("/api/v1")
    health = client.get("/api/v1/health")

    assert discovery.status_code == 200
    assert health.status_code == 200
    assert health.get_json()["data"]["status"] == "ok"


def test_release_smoke_covers_primary_web_and_api_entries(monkeypatch):
    monkeypatch.delenv("TASK_MANAGER_API_TOKEN", raising=False)
    client = app.test_client()
    paths = ["/", "/today/", "/reminders/", "/board/", "/calendar/", "/api/v1", "/api/v1/health"]

    results = {path: client.get(path).status_code for path in paths}

    assert results == {path: 200 for path in paths}
