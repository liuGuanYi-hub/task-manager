"""显式项目管理路由"""
from flask import Blueprint, redirect, render_template, request, url_for

from models.project import Project
from models.task import Status
from storage.json_storage import JSONStorage


projects_bp = Blueprint("projects", __name__, url_prefix="/projects")


def _project_summary(storage: JSONStorage, project: Project) -> dict:
    """计算单个项目的任务进度。"""
    tasks = storage.get_all(project_id=project.id)
    completed = sum(1 for task in tasks if task.status == Status.DONE)
    total = len(tasks)
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "total_tasks": total,
        "completed_tasks": completed,
        "completion_rate": round((completed / total * 100), 1) if total else 0,
    }


@projects_bp.route("/")
def projects_list():
    """项目列表，不再从任务标签推导项目。"""
    storage = JSONStorage()
    projects = [_project_summary(storage, project) for project in storage.get_projects()]
    projects.sort(key=lambda project: project["id"])
    return render_template("projects.html", projects=projects)


@projects_bp.route("/new", methods=["GET", "POST"])
def new_project():
    """创建项目。"""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            return "项目名称不能为空", 400

        project = Project(
            name=name,
            description=request.form.get("description", "").strip(),
        )
        storage = JSONStorage()
        created = storage.add_project(project)
        return redirect(url_for("projects.project_detail", project_id=created.id))

    return render_template("project_form.html", mode="new", action=url_for("projects.new_project"), project=None)


@projects_bp.route("/<int:project_id>")
def project_detail(project_id: int):
    """项目详情，只显示当前项目关联的任务。"""
    storage = JSONStorage()
    project = storage.get_project_by_id(project_id)
    if project is None:
        return "项目不存在", 404

    tasks = storage.get_all(project_id=project_id)
    completed = sum(1 for task in tasks if task.status == Status.DONE)
    total = len(tasks)
    completion_rate = round((completed / total * 100), 1) if total else 0

    return render_template(
        "project_detail.html",
        project=project,
        tasks=tasks,
        total=total,
        completed=completed,
        completion_rate=completion_rate,
    )


@projects_bp.route("/<int:project_id>/edit")
def edit_project(project_id: int):
    """编辑项目页面。"""
    project = JSONStorage().get_project_by_id(project_id)
    if project is None:
        return "项目不存在", 404
    return render_template(
        "project_form.html",
        mode="edit",
        action=url_for("projects.update_project", project_id=project_id),
        project=project,
    )


@projects_bp.route("/<int:project_id>/update", methods=["POST"])
def update_project(project_id: int):
    """更新项目。"""
    storage = JSONStorage()
    project = storage.get_project_by_id(project_id)
    if project is None:
        return "项目不存在", 404

    name = request.form.get("name", "").strip()
    if not name:
        return "项目名称不能为空", 400
    project.name = name
    project.description = request.form.get("description", "").strip()
    storage.update_project(project)
    return redirect(url_for("projects.project_detail", project_id=project_id))
