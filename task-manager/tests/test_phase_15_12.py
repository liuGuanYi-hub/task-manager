import json
from pathlib import Path

import pytest

from scripts import release_smoke


APP_ROOT = Path(__file__).resolve().parents[1]


def test_release_smoke_script_declares_isolated_runtime_contract():
    script = (APP_ROOT / "scripts" / "release_smoke.py").read_text(encoding="utf-8")

    assert "TASK_MANAGER_STORAGE" in script
    assert "TASK_MANAGER_SQLITE_PATH" in script
    assert "TASK_MANAGER_API_TOKEN" in script
    assert "output" in script and "release-smoke" in script
    assert "playwright-cli" in script
    assert "test-only-token" in script
    assert "RELEASE_SMOKE_PASSED" in script
    assert "RELEASE_SMOKE_FAILED" in script
    assert "summary.json" in script
    assert "server_stderr_tail" in script


def test_release_smoke_is_documented_and_artifacts_are_ignored():
    readme = (APP_ROOT / "README.md").read_text(encoding="utf-8")
    deploy = (APP_ROOT / "DEPLOY.md").read_text(encoding="utf-8")
    gitignore = (APP_ROOT / ".gitignore").read_text(encoding="utf-8")

    assert "release_smoke.py" in readme
    assert "release_smoke.py" in deploy
    assert "output/release-smoke/" in gitignore


def test_port_diagnostic_reports_occupied_range(monkeypatch):
    class BusySocket:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def bind(self, _address):
            raise OSError("address already in use")

    monkeypatch.setattr(release_smoke.socket, "socket", lambda *_args, **_kwargs: BusySocket())

    with pytest.raises(RuntimeError) as error:
        release_smoke._find_port()

    message = str(error.value)
    assert "5084-5119" in message
    assert "5119" in message
    assert "address already in use" in message


def test_smoke_summary_helper_writes_machine_readable_evidence(tmp_path):
    log_path = tmp_path / "server.stderr.log"
    log_path.write_text("first line\nlast line", encoding="utf-8")

    release_smoke._write_summary(
        tmp_path,
        {"status": "failed", "server_exit_code": 1, "server_stderr_tail": release_smoke._tail_text(log_path)},
    )

    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert summary["status"] == "failed"
    assert summary["server_exit_code"] == 1
    assert summary["server_stderr_tail"] == "first line\nlast line"
