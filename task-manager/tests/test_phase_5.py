"""阶段 5：归档、恢复、备份和导入校验测试"""
import io
import json

import pytest
from click.testing import CliRunner

from commands.delete import delete_task
from models.project import Project
from models.saved_view import SavedView
from models.task import Task
from storage.json_storage import ImportValidationError, JSONStorage
from web_app import app


def test_invalid_import_keeps_existing_file_unchanged(tmp_path):
    path = tmp_path / "tasks.json"
    storage = JSONStorage(path)
    storage.add(Task(title="原有任务"))
    before = path.read_bytes()

    with pytest.raises(ImportValidationError):
        storage.import_payload({"tasks": [{"id": 1, "priority": "坏优先级"}]})

    assert path.read_bytes() == before
    assert storage.get_by_id(1).title == "原有任务"


def test_import_remap_preserves_existing_data_and_relationships(tmp_path):
    path = tmp_path / "tasks.json"
    storage = JSONStorage(path)
    existing_project = storage.add_project(Project(name="原有项目"))
    existing_task = storage.add(Task(title="原有任务", project_id=existing_project.id))
    storage.add_saved_view(SavedView(name="原有视图", filters={"project_id": existing_project.id}))

    result = storage.import_payload(
        {
            "schema_version": 1,
            "projects": [{"id": existing_project.id, "name": "导入项目"}],
            "tasks": [{"id": existing_task.id, "title": "导入任务", "project_id": existing_project.id}],
            "saved_views": [{"id": 1, "name": "导入视图", "filters": {"project_id": existing_project.id}}],
        },
        conflict="remap",
    )

    imported_project = next(project for project in storage.get_projects() if project.name == "导入项目")
    imported_task = next(task for task in storage.get_all(include_archived=True) if task.title == "导入任务")
    imported_view = next(view for view in storage.get_saved_views() if view.name == "导入视图")
    assert result["remapped_tasks"] == 1
    assert imported_project.id != existing_project.id
    assert imported_task.id != existing_task.id
    assert imported_task.project_id == imported_project.id
    assert imported_view.filters["project_id"] == imported_project.id
    assert storage.get_by_id(existing_task.id).title == "原有任务"


def test_import_replace_and_skip_conflicts(tmp_path):
    replace_storage = JSONStorage(tmp_path / "replace.json")
    replace_storage.add(Task(title="旧任务"))
    replace_storage.import_payload(
        {"tasks": [{"id": 1, "title": "覆盖任务"}]},
        conflict="replace",
    )
    assert [task.title for task in replace_storage.get_all()] == ["覆盖任务"]

    skip_storage = JSONStorage(tmp_path / "skip.json")
    skip_storage.add(Task(title="保留任务"))
    result = skip_storage.import_payload(
        {"tasks": [{"id": 1, "title": "不应导入"}]},
        conflict="skip",
    )
    assert result["skipped_tasks"] == 1
    assert skip_storage.get_by_id(1).title == "保留任务"


def test_cli_delete_archives_by_default(tmp_path, monkeypatch):
    path = tmp_path / "tasks.json"
    storage = JSONStorage(path)
    storage.add(Task(title="命令行归档"))
    monkeypatch.setattr("commands.delete.JSONStorage", lambda: storage)

    result = CliRunner().invoke(delete_task, ["1", "-y"])

    assert result.exit_code == 0
    assert "已归档" in result.output
    assert storage.get_all() == []
    assert storage.get_archived()[0].title == "命令行归档"


def test_web_delete_archives_and_archive_page_restores(tmp_path, monkeypatch):
    path = tmp_path / "tasks.json"
    storage = JSONStorage(path)
    task = storage.add(Task(title="Web 归档"))
    monkeypatch.setattr("web_app.storage", storage)
    monkeypatch.setattr("routes.archive_routes.JSONStorage", lambda: storage)
    client = app.test_client()

    archived = client.post(f"/task/{task.id}/delete")
    assert archived.status_code == 302
    assert storage.get_all() == []
    assert client.get("/archive").status_code == 200

    restored = client.post(f"/archive/{task.id}/restore")
    assert restored.status_code == 302
    assert storage.get_all()[0].title == "Web 归档"


def test_backup_contains_archived_tasks_projects_and_views(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    project = storage.add_project(Project(name="备份项目"))
    task = storage.add(Task(title="备份归档任务", project_id=project.id))
    storage.archive(task.id)
    storage.add_saved_view(SavedView(name="备份视图", filters={"project_id": project.id}))
    monkeypatch.setattr("routes.settings_routes.JSONStorage", lambda: storage)

    response = app.test_client().get("/settings/backup")

    assert response.status_code == 200
    payload = json.loads(response.get_data(as_text=True))
    assert payload["backup"] is True
    assert payload["tasks"][0]["archived"] is True
    assert payload["projects"][0]["name"] == "备份项目"
    assert payload["saved_views"][0]["name"] == "备份视图"


def test_web_import_invalid_file_does_not_change_tasks(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    storage.add(Task(title="导入前任务"))
    monkeypatch.setattr("routes.settings_routes.JSONStorage", lambda: storage)

    response = app.test_client().post(
        "/settings/import",
        data={"conflict": "remap", "backup_file": (io.BytesIO(b"not-json"), "bad.json")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert [task.title for task in storage.get_all()] == ["导入前任务"]
