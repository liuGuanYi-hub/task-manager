"""阶段 15.3：JSON 导入预览与冲突统计。"""

import io
import json

from models.task import Task
from storage.json_storage import JSONStorage
from web_app import app


def test_preview_import_reports_conflicts_without_writing_file(tmp_path):
    storage_path = tmp_path / "tasks.json"
    storage = JSONStorage(storage_path)
    original = storage.add(Task(title="预览前任务"))
    before_bytes = storage_path.read_bytes()
    payload = storage.export_payload()

    result = storage.preview_import(payload, conflict="remap")

    assert result["preview"] is True
    assert result["incoming"]["tasks"] == 1
    assert result["conflicts"]["tasks"] == 1
    assert result["remapped_tasks"] == 1
    assert result["after"]["tasks"] == 2
    assert storage_path.read_bytes() == before_bytes
    assert [task.title for task in storage.get_all()] == [original.title]


def test_settings_import_preview_renders_summary_and_keeps_data(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    storage.add(Task(title="设置页原任务"))
    payload = storage.export_payload()
    monkeypatch.setattr("routes.settings_routes.JSONStorage", lambda: storage)

    response = app.test_client().post(
        "/settings/import",
        data={
            "mode": "preview",
            "conflict": "remap",
            "backup_file": (io.BytesIO(json.dumps(payload, ensure_ascii=False).encode("utf-8")), "preview.json"),
        },
        content_type="multipart/form-data",
    )
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "导入预览（未写入）" in body
    assert "冲突 1" in body
    assert "当前数据文件没有被修改" in body
    assert len(storage.get_all()) == 1


def test_settings_import_confirmation_still_writes_after_preview(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    storage.add(Task(title="确认前任务"))
    payload = storage.export_payload()
    payload["tasks"][0]["id"] = 9
    payload["tasks"][0]["title"] = "确认写入任务"
    monkeypatch.setattr("routes.settings_routes.JSONStorage", lambda: storage)

    response = app.test_client().post(
        "/settings/import",
        data={
            "mode": "import",
            "conflict": "remap",
            "backup_file": (io.BytesIO(json.dumps(payload, ensure_ascii=False).encode("utf-8")), "confirm.json"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 302
    assert len(storage.get_all()) == 2
    assert any(task.title == "确认写入任务" for task in storage.get_all())
