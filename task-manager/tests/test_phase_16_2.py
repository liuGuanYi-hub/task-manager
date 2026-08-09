"""阶段 16.2：统一网页错误页和 API 错误边界。"""

from web_app import app, handle_internal_error


def test_unknown_web_route_renders_recoverable_error_page():
    response = app.test_client().get("/route-that-does-not-exist")
    body = response.get_data(as_text=True) if hasattr(response, "get_data") else response

    assert response.status_code == 404
    assert "页面没有找到" in body
    assert "SAFE RECOVERY" in body
    assert 'href="/"' in body
    assert "Traceback" not in body


def test_unknown_api_route_keeps_json_error_contract(monkeypatch):
    monkeypatch.delenv("TASK_MANAGER_API_TOKEN", raising=False)

    response = app.test_client().get("/api/v1/route-that-does-not-exist")

    assert response.status_code == 404
    assert response.is_json
    assert response.get_json() == {
        "error": {"code": "not_found", "message": "资源不存在"}
    }


def test_internal_web_error_hides_exception_details():
    with app.test_request_context("/broken-page"):
        response, status = handle_internal_error(RuntimeError("secret implementation detail"))

    body = response.get_data(as_text=True) if hasattr(response, "get_data") else response
    assert status == 500
    assert "页面暂时无法打开" in body
    assert "secret implementation detail" not in body


def test_internal_api_error_keeps_json_error_contract():
    with app.test_request_context("/api/v1/broken"):
        response, status = handle_internal_error(RuntimeError("secret implementation detail"))

    assert status == 500
    assert response.get_json() == {
        "error": {"code": "internal_error", "message": "服务器暂时无法处理请求"}
    }


def test_error_template_and_styles_are_available():
    client = app.test_client()
    template_response = client.get("/static/app.css")
    body = template_response.get_data(as_text=True)

    assert template_response.status_code == 200
    assert ".error-page" in body
    assert ".error-code" in body
