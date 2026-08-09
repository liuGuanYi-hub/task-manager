"""阶段 15.12：隔离的本地 SQLite/API/浏览器发布 smoke。"""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

APP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_ROOT))

from models.project import Project
from models.task import Task
from storage.sqlite_storage import SQLiteStorage


API_TOKEN = "test-only-token"
NPX_COMMAND = shutil.which("npx.cmd") or shutil.which("npx")


def _assert_equal(name: str, actual: object, expected: object) -> None:
    if actual != expected:
        raise AssertionError(f"{name} 不符合预期：实际 {actual}，预期 {expected}")


def _request_json(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    payload: dict | None = None,
) -> tuple[int, dict]:
    body = None
    request_headers = dict(headers or {})
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request_headers["Content-Type"] = "application/json"
    request = Request(url, data=body, headers=request_headers, method=method)
    try:
        with urlopen(request, timeout=10) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        return error.code, json.loads(error.read().decode("utf-8"))
    except URLError as error:
        raise RuntimeError(f"HTTP smoke 请求失败：{url}: {error}") from error


def _find_port() -> int:
    for port in range(5084, 5120):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            try:
                probe.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise RuntimeError("没有找到可用的本地 smoke 端口")


def _run_playwright(run_root: Path, session: str, *arguments: str) -> None:
    if not NPX_COMMAND:
        raise RuntimeError("未找到 npx.cmd/npx，请先安装 Node.js/npm")
    command = [
        NPX_COMMAND,
        "--yes",
        "--package",
        "@playwright/cli",
        "playwright-cli",
        f"-s={session}",
        *arguments,
    ]
    completed = subprocess.run(command, cwd=run_root, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"Playwright 命令失败：{' '.join(arguments)}")


def main() -> int:
    app_root = APP_ROOT
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_root = app_root / "output" / "release-smoke" / f"run-{run_id}"
    run_root.mkdir(parents=True, exist_ok=False)
    db_path = run_root / "runtime.db"
    empty_fixture = run_root / "empty.json"
    empty_fixture.write_bytes(b"")
    stdout_handle = (run_root / "server.stdout.log").open("w", encoding="utf-8")
    stderr_handle = (run_root / "server.stderr.log").open("w", encoding="utf-8")
    server = None
    session = f"release-smoke-{run_id}"

    try:
        if not NPX_COMMAND:
            raise RuntimeError("未找到 npx.cmd/npx，请先安装 Node.js/npm")
        storage = SQLiteStorage(db_path)
        project = storage.add_project(Project(name="发布 smoke 项目"))
        storage.add(Task(title="发布 smoke 任务", project_id=project.id))

        environment = os.environ.copy()
        environment.update(
            {
                "TASK_MANAGER_STORAGE": "sqlite",
                "TASK_MANAGER_SQLITE_PATH": str(db_path),
                "TASK_MANAGER_API_TOKEN": API_TOKEN,
            }
        )
        port = _find_port()
        base_url = f"http://127.0.0.1:{port}"
        server = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "flask",
                "--app",
                "web_app:app",
                "run",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
            ],
            cwd=app_root,
            env=environment,
            stdout=stdout_handle,
            stderr=stderr_handle,
        )

        health = None
        for _ in range(30):
            try:
                status, health = _request_json(f"{base_url}/api/v1/health")
                if status == 200:
                    break
            except RuntimeError:
                pass
            time.sleep(0.25)
        if not health or health.get("data", {}).get("backend") != "sqlite":
            raise RuntimeError("Flask SQLite 服务未在预期时间内启动")

        with urlopen(f"{base_url}/settings/", timeout=10) as settings_response:
            settings_status = settings_response.status
            settings_html = settings_response.read().decode("utf-8")
        _assert_equal("设置页状态", settings_status, 200)
        if "总任务数" not in settings_html or "项目数" not in settings_html:
            raise AssertionError("设置页没有渲染 SQLite 统计信息")

        unauthorized_status, unauthorized = _request_json(f"{base_url}/api/v1/tasks")
        _assert_equal("未授权任务接口", unauthorized_status, 401)
        _assert_equal("未授权错误码", unauthorized["error"]["code"], "authentication_required")

        auth_headers = {"Authorization": f"Bearer {API_TOKEN}"}
        authorized_status, authorized = _request_json(
            f"{base_url}/api/v1/tasks?page=1&page_size=1",
            headers=auth_headers,
        )
        _assert_equal("授权任务接口", authorized_status, 200)
        _assert_equal("授权任务总数", authorized["meta"]["total"], 1)
        _assert_equal("授权任务标题", authorized["data"][0]["title"], "发布 smoke 任务")

        invalid_status, invalid = _request_json(
            f"{base_url}/api/v1/tasks",
            method="POST",
            headers=auth_headers,
            payload={"title": ""},
        )
        _assert_equal("无效任务接口", invalid_status, 400)
        _assert_equal("无效任务错误码", invalid["error"]["code"], "invalid_request")

        _run_playwright(run_root, session, "open", f"{base_url}/settings/")
        _run_playwright(run_root, session, "snapshot")
        browser_path = json.dumps(str(empty_fixture))
        browser_check = (
            "async (page) => { "
            f"await page.locator('input[type=file]').setInputFiles({browser_path}); "
            "await page.getByRole('button', { name: '先预览' }).click(); "
            "const alertText = (await page.getByRole('alert').textContent()).trim(); "
            "const bodyText = await page.locator('body').innerText(); "
            "if (alertText !== '导入文件不能为空') throw new Error('空备份错误提示不正确: ' + alertText); "
            "if (!bodyText.includes('总任务数') || !bodyText.includes('项目数')) throw new Error('SQLite 统计未渲染'); "
            "if (!bodyText.includes('单个备份文件不能超过 5 MB')) throw new Error('导入边界提示未渲染'); "
            "console.log(JSON.stringify({ alert: alertText, sqliteStats: true })); "
            "}"
        )
        _run_playwright(run_root, session, "run-code", browser_check)
        _run_playwright(run_root, session, "screenshot")

        print("RELEASE_SMOKE_PASSED")
        print("backend=sqlite")
        print("api=health-200 unauthorized-401 authorized-200 invalid-400")
        print("browser=empty-import-400")
        print(f"evidence={run_root}")
        return 0
    finally:
        try:
            _run_playwright(run_root, session, "close")
        except Exception:
            pass
        if server is not None:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
        stdout_handle.close()
        stderr_handle.close()


if __name__ == "__main__":
    raise SystemExit(main())
