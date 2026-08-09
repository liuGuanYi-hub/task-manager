"""阶段 15.9：无效/损坏备份的错误提示与写入安全边界。"""

import io
import json

import pytest

from models.task import Task
from storage.json_storage import JSONStorage
from web_app import app


def _post_raw(client, raw, filename, conflict="remap", mode="preview"):
    return client.post(
        "/settings/import",
        data={
            "mode": mode,
            "conflict": conflict,
            "backup_file": (io.BytesIO(raw), filename),
        },
        content_type="multipart/form-data",
    )


@pytest.mark.parametrize(
    ("raw", "filename", "expected"),
    [
        (b"{not-json", "broken.json", "导入文件不是有效的 UTF-8 JSON"),
        (b"\xff\xfe\xfd", "broken-encoding.json", "导入文件不是有效的 UTF-8 JSON"),
        (json.dumps([], ensure_ascii=False).encode("utf-8"), "wrong-root.json", "导入文件必须是 JSON 对象"),
    ],
)
def test_invalid_backup_keeps_storage_and_selected_strategy(
    tmp_path,
    monkeypatch,
    raw,
    filename,
    expected,
):
    storage = JSONStorage(tmp_path / "isolated.json")
    storage.add(Task(title="损坏备份前任务"))
    before = storage.db_path.read_bytes()
    monkeypatch.setattr("routes.settings_routes.JSONStorage", lambda: storage)

    response = _post_raw(
        app.test_client(),
        raw,
        filename,
        conflict="skip",
    )
    body = response.get_data(as_text=True)

    assert response.status_code == 400
    assert expected in body
    assert 'option value="skip" selected' in body
    assert 'option value="remap" selected' not in body
    assert storage.db_path.read_bytes() == before
    assert [task.title for task in storage.get_all()] == ["损坏备份前任务"]


def test_invalid_record_does_not_write_and_preserves_replace_strategy(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "invalid-record.json")
    storage.add(Task(title="结构校验前任务"))
    before = storage.db_path.read_bytes()
    monkeypatch.setattr("routes.settings_routes.JSONStorage", lambda: storage)

    payload = {
        "schema_version": 1,
        "tasks": [{"id": 1, "title": ""}],
        "projects": [],
        "saved_views": [],
    }
    response = _post_raw(
        app.test_client(),
        json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        "invalid-record.json",
        conflict="replace",
        mode="import",
    )
    body = response.get_data(as_text=True)

    assert response.status_code == 400
    assert "字段 tasks[0] 缺少有效标题" in body
    assert 'option value="replace" selected' in body
    assert 'option value="remap" selected' not in body
    assert storage.db_path.read_bytes() == before
    assert [task.title for task in storage.get_all()] == ["结构校验前任务"]
