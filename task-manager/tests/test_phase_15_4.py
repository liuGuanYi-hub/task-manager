"""阶段 15.4：JSON/SQLite 双后端备份恢复 smoke。"""

import io
import json

import pytest

from models.project import Project
from models.saved_view import SavedView
from models.task import Status, Task
from storage.json_storage import JSONStorage
from storage.sqlite_storage import SQLiteStorage
from web_app import app


BACKENDS = [JSONStorage, SQLiteStorage]


def _seed_backup(storage):
    project = storage.add_project(Project(name="backup-project", description="cross-backend"))
    task = storage.add(
        Task(
            title="backup-task",
            description="restore me",
            status=Status.DONE,
            tags=["backup", "smoke"],
            project_id=project.id,
        )
    )
    storage.archive(task.id)
    storage.add_saved_view(SavedView(name="backup-view", filters={"project_id": project.id}))
    return project, task


@pytest.mark.parametrize("backend_cls", BACKENDS)
def test_preview_import_is_read_only_for_json_and_sqlite(tmp_path, backend_cls):
    path = tmp_path / ("preview.json" if backend_cls is JSONStorage else "preview.db")
    storage = backend_cls(path)
    _seed_backup(storage)
    payload = storage.export_payload()
    before_bytes = path.read_bytes()

    result = storage.preview_import(payload, conflict="remap")

    assert result["preview"] is True
    assert result["incoming"] == {"tasks": 1, "projects": 1, "saved_views": 1}
    assert result["conflicts"] == {"tasks": 1, "projects": 1, "saved_views": 1}
    assert result["after"] == {"tasks": 2, "projects": 2, "saved_views": 2}
    assert result["remapped_tasks"] == 1
    assert result["remapped_views"] == 1
    assert path.read_bytes() == before_bytes
    assert len(storage.get_all(include_archived=True)) == 1
    assert len(storage.get_projects()) == 1
    assert len(storage.get_saved_views()) == 1


@pytest.mark.parametrize("source_cls", BACKENDS)
@pytest.mark.parametrize("target_cls", BACKENDS)
def test_backup_restores_between_json_and_sqlite(tmp_path, source_cls, target_cls):
    source_path = tmp_path / ("source.json" if source_cls is JSONStorage else "source.db")
    target_path = tmp_path / ("target.json" if target_cls is JSONStorage else "target.db")
    source = source_cls(source_path)
    source_project, source_task = _seed_backup(source)

    target = target_cls(target_path)
    result = target.import_payload(source.export_payload(), conflict="remap")

    assert result["tasks"] == 1
    assert result["projects"] == 1
    assert result["saved_views"] == 1
    restored_task = target.get_all(include_archived=True)[0]
    restored_project = target.get_project_by_id(restored_task.project_id)
    restored_view = target.get_saved_views()[0]
    assert restored_task.title == source_task.title
    assert restored_task.archived is True
    assert restored_task.status is Status.DONE
    assert restored_task.tags == source_task.tags
    assert restored_project.name == source_project.name
    assert restored_view.filters == {"project_id": restored_project.id}

    reloaded = target_cls(target_path)
    assert reloaded.get_all(include_archived=True)[0].archived is True
    assert reloaded.get_saved_views()[0].filters == {"project_id": restored_project.id}


def test_settings_preview_uses_sqlite_storage_without_writing(tmp_path, monkeypatch):
    storage = SQLiteStorage(tmp_path / "settings.db")
    _seed_backup(storage)
    payload = storage.export_payload()
    before_bytes = storage.db_path.read_bytes()
    monkeypatch.setattr("routes.settings_routes.JSONStorage", lambda: storage)

    response = app.test_client().post(
        "/settings/import",
        data={
            "mode": "preview",
            "conflict": "remap",
            "backup_file": (
                io.BytesIO(json.dumps(payload, ensure_ascii=False).encode("utf-8")),
                "sqlite-preview.json",
            ),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert "导入预览" in response.get_data(as_text=True)
    assert storage.db_path.read_bytes() == before_bytes
    assert len(storage.get_all(include_archived=True)) == 1
