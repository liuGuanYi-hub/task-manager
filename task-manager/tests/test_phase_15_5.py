"""阶段 15.5：导入冲突说明与备份恢复演练 UI。"""

from pathlib import Path

from storage.json_storage import JSONStorage
from web_app import app


def test_settings_page_renders_conflict_guide_and_recovery_drill(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "settings.json")
    monkeypatch.setattr("routes.settings_routes.JSONStorage", lambda: storage)

    response = app.test_client().get("/settings/")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'data-conflict-select' in body
    assert 'data-conflict-strategy' in body
    assert 'data-recovery-drill' in body
    assert 'data-recovery-step="backup"' in body
    assert 'data-recovery-step="verify"' in body
    assert 'settings.js' in body
    assert 'rel="icon" href="data:,"' in body
    assert "仅保存在当前浏览器" in body


def test_settings_script_contains_all_conflict_modes_and_local_recovery_state():
    script_path = Path(__file__).resolve().parents[1] / "static" / "settings.js"
    script = script_path.read_text(encoding="utf-8")

    assert 'remap:' in script
    assert 'skip:' in script
    assert 'replace:' in script
    assert "task-manager-recovery-drill-v1" in script
    assert "localStorage.setItem" in script
    assert "localStorage.removeItem" in script
