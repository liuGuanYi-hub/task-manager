"""阶段 2：显式项目实体和项目级任务隔离测试"""
import json
import importlib

import pytest
from click.testing import CliRunner

from commands.create import create_task
from commands.list_tasks import list_tasks
from commands.projects import create_project
from models.project import Project
from models.task import Task
from storage.json_storage import JSONStorage
from web_app import app


def test_legacy_task_without_project_keeps_unassigned_state():
    task = Task.from_dict({"id": 1, "title": "历史任务", "tags": ["学习"]})

    assert task.project_id is None
    assert task.to_dict()["project_id"] is None


def test_project_storage_and_task_isolation(tmp_path):
    storage = JSONStorage(tmp_path / "tasks.json")
    study = storage.add_project(Project(name="学习项目", description="阶段 2"))
    work = storage.add_project(Project(name="工作项目"))

    study_task = storage.add(Task(title="学习任务", project_id=study.id, tags=["学习"]))
    work_task = storage.add(Task(title="工作任务", project_id=work.id, tags=["学习"]))
    free_task = storage.add(Task(title="未归属任务", tags=["学习"]))

    assert [task.title for task in storage.get_all(project_id=study.id)] == [study_task.title]
    assert [task.title for task in storage.get_all(project_id=work.id)] == [work_task.title]
    assert [task.title for task in storage.get_all(project_id=None)] == [free_task.title]
    assert [task.title for task in storage.query(project_id=study.id, tag="学习")] == ["学习任务"]

    with pytest.raises(ValueError, match="项目不存在"):
        storage.add(Task(title="错误关联", project_id=999))

    reloaded = JSONStorage(tmp_path / "tasks.json")
    assert reloaded.get_project_by_id(study.id).name == "学习项目"
    assert reloaded.get_by_id(study_task.id).project_id == study.id


def test_project_creation_cli_and_task_project_option(tmp_path, monkeypatch):
    storage_path = tmp_path / "tasks.json"
    monkeypatch.setattr(
        "commands.projects.JSONStorage",
        lambda: JSONStorage(storage_path),
    )
    project_result = CliRunner().invoke(create_project, ["命令行项目", "-d", "项目描述"])
    assert project_result.exit_code == 0

    monkeypatch.setattr(
        "commands.create.JSONStorage",
        lambda: JSONStorage(storage_path),
    )
    task_result = CliRunner().invoke(
        create_task,
        ["项目任务", "--project-id", "1", "--tag", "分类"],
    )

    assert task_result.exit_code == 0
    saved = JSONStorage(storage_path).get_all(project_id=1)[0]
    assert saved.title == "项目任务"
    assert saved.project_id == 1


def test_list_cli_can_isolate_project_tasks(tmp_path, monkeypatch):
    storage_path = tmp_path / "tasks.json"
    storage = JSONStorage(storage_path)
    project = storage.add_project(Project(name="目标项目"))
    storage.add(Task(title="项目内任务", project_id=project.id))
    storage.add(Task(title="项目外任务"))
    list_tasks_module = importlib.import_module("commands.list_tasks")
    monkeypatch.setattr(list_tasks_module, "JSONStorage", lambda: JSONStorage(storage_path))

    result = CliRunner().invoke(list_tasks, ["--project-id", str(project.id)])

    assert result.exit_code == 0
    assert "项目内任务" in result.output
    assert "项目外任务" not in result.output


def test_web_project_detail_only_shows_project_tasks(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    project = storage.add_project(Project(name="Web 项目", description="详情页测试"))
    storage.add(Task(title="项目内任务", project_id=project.id))
    storage.add(Task(title="无项目任务"))
    monkeypatch.setattr("routes.projects_routes.JSONStorage", lambda: storage)

    response = app.test_client().get(f"/projects/{project.id}")

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "项目内任务" in body
    assert "无项目任务" not in body


def test_web_create_task_can_assign_project(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    project = storage.add_project(Project(name="表单项目"))
    monkeypatch.setattr("web_app.storage", storage)

    response = app.test_client().post(
        "/new",
        data={"title": "表单项目任务", "project_id": str(project.id)},
    )

    assert response.status_code == 302
    assert storage.get_all(project_id=project.id)[0].title == "表单项目任务"


def test_json_export_contains_projects(tmp_path, monkeypatch):
    storage = JSONStorage(tmp_path / "tasks.json")
    project = storage.add_project(Project(name="导出项目"))
    storage.add(Task(title="导出任务", project_id=project.id))
    monkeypatch.setattr("routes.settings_routes.JSONStorage", lambda: storage)

    response = app.test_client().get("/settings/export/json")

    assert response.status_code == 200
    exported = json.loads(response.get_data(as_text=True))
    assert exported["projects"][0]["name"] == "导出项目"
    assert exported["tasks"][0]["project_id"] == project.id
