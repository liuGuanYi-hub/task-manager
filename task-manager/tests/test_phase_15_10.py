"""阶段 15.10：导入大小限制、空文件和 JSON/SQLite 错误契约。"""

import io
import json

import pytest

from models.task import Task
from routes.settings_routes import MAX_IMPORT_BYTES
from storage.json_storage import JSONStorage
from storage.sqlite_storage import SQLiteStorage
from web_app import app


BACKENDS = [JSONStorage, SQLiteStorage]


def _post_raw(client, raw, filename, conflict="replace", mode="import"):
    return client.post(
        "/settings/import",
        data={
            "mode": mode,
            "conflict": conflict,
            "backup_file": (io.BytesIO(raw), filename),
        },
        content_type="multipart/form-data",
    )


@pytest.mark.parametrize("backend_cls", BACKENDS)
def test_empty_backup_has_clear_error_and_keeps_backend_unchanged(tmp_path, monkeypatch, backend_cls):
    path = tmp_path / ("empty.json" if backend_cls is JSONStorage else "empty.db")
    storage = backend_cls(path)
    storage.add(Task(title="空文件前任务"))
    before = path.read_bytes()
    monkeypatch.setattr("routes.settings_routes.JSONStorage", lambda: storage)

    response = _post_raw(app.test_client(), b"", "empty.json")
    body = response.get_data(as_text=True)

    assert response.status_code == 400
    assert "导入文件不能为空" in body
    assert 'option value="replace" selected' in body
    assert path.read_bytes() == before
    assert [task.title for task in storage.get_all()] == ["空文件前任务"]


@pytest.mark.parametrize("backend_cls", BACKENDS)
def test_oversized_backup_is_rejected_before_json_decode(tmp_path, monkeypatch, backend_cls):
    path = tmp_path / ("oversize.json" if backend_cls is JSONStorage else "oversize.db")
    storage = backend_cls(path)
    storage.add(Task(title="超限前任务"))
    before = path.read_bytes()
    monkeypatch.setattr("routes.settings_routes.JSONStorage", lambda: storage)

    response = _post_raw(
        app.test_client(),
        b"x" * (MAX_IMPORT_BYTES + 1),
        "oversize.json",
        conflict="skip",
    )
    body = response.get_data(as_text=True)

    assert response.status_code == 400
    assert "导入文件不能超过 5 MB" in body
    assert 'option value="skip" selected' in body
    assert path.read_bytes() == before
    assert [task.title for task in storage.get_all()] == ["超限前任务"]


@pytest.mark.parametrize("backend_cls", BACKENDS)
def test_schema_version_error_is_consistent_between_backends(tmp_path, monkeypatch, backend_cls):
    path = tmp_path / ("version.json" if backend_cls is JSONStorage else "version.db")
    storage = backend_cls(path)
    storage.add(Task(title="版本前任务"))
    before = path.read_bytes()
    monkeypatch.setattr("routes.settings_routes.JSONStorage", lambda: storage)

    response = _post_raw(
        app.test_client(),
        json.dumps({"schema_version": 99}).encode("utf-8"),
        "unsupported-version.json",
        conflict="skip",
    )
    body = response.get_data(as_text=True)

    assert response.status_code == 400
    assert "不支持的备份版本" in body
    assert 'option value="skip" selected' in body
    assert path.read_bytes() == before
    assert [task.title for task in storage.get_all()] == ["版本前任务"]
