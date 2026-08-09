from pathlib import Path


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


def test_release_smoke_is_documented_and_artifacts_are_ignored():
    readme = (APP_ROOT / "README.md").read_text(encoding="utf-8")
    deploy = (APP_ROOT / "DEPLOY.md").read_text(encoding="utf-8")
    gitignore = (APP_ROOT / ".gitignore").read_text(encoding="utf-8")

    assert "release_smoke.py" in readme
    assert "release_smoke.py" in deploy
    assert "output/release-smoke/" in gitignore
