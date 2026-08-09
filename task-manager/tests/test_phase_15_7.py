"""阶段 15.7：隔离后端上的导入预览与确认写入回归。"""

import io
import json

from storage.json_storage import JSONStorage
from web_app import app


def _browser_backup_payload():
    timestamp = "2026-08-09T23:16:00"
    return {
        "schema_version": 1,
        "backup": True,
        "tasks": [
            {
                "id": 101,
                "title": "phase-15-7-restored-task",
                "description": "isolated browser recovery smoke",
                "created_at": timestamp,
                "updated_at": timestamp,
                "archived": False,
                "tags": ["browser", "recovery"],
                "project_id": 201,
            }
        ],
        "projects": [
            {
                "id": 201,
                "name": "phase-15-7-project",
                "description": "isolated browser recovery smoke",
                "created_at": timestamp,
                "updated_at": timestamp,
            }
        ],
        "saved_views": [
            {
                "id": 301,
                "name": "phase-15-7-view",
                "filters": {"project_id": 201},
                "created_at": timestamp,
                "updated_at": timestamp,
            }
        ],
        "next_id": 102,
        "next_project_id": 202,
        "next_view_id": 302,
    }


def _post_import(client, payload, mode):
    return client.post(
        "/settings/import",
        data={
            "mode": mode,
            "conflict": "remap",
            "backup_file": (
                io.BytesIO(json.dumps(payload, ensure_ascii=False).encode("utf-8")),
                "phase-15-7-backup.json",
            ),
        },
        content_type="multipart/form-data",
    )


def test_isolated_import_preview_then_confirm_writes_only_after_confirmation(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "isolated.json")
    payload = _browser_backup_payload()
    monkeypatch.setattr("routes.settings_routes.JSONStorage", lambda: storage)
    client = app.test_client()

    preview = _post_import(client, payload, "preview")

    assert preview.status_code == 200
    assert "导入预览" in preview.get_data(as_text=True)
    assert not storage.db_path.exists()

    confirmation = _post_import(client, payload, "import")

    assert confirmation.status_code == 302
    reloaded = JSONStorage(storage.db_path)
    assert len(reloaded.get_all(include_archived=True)) == 1
    assert len(reloaded.get_projects()) == 1
    assert len(reloaded.get_saved_views()) == 1
    task = reloaded.get_all(include_archived=True)[0]
    assert task.title == "phase-15-7-restored-task"
    assert task.project_id == reloaded.get_projects()[0].id
    assert reloaded.get_saved_views()[0].filters == {"project_id": task.project_id}
