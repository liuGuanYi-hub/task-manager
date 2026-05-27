"""项目管理路由"""
from flask import Blueprint, render_template, redirect, url_for
from storage.json_storage import JSONStorage
from models.task import Status

projects_bp = Blueprint("projects", __name__, url_prefix="/projects")


@projects_bp.route("/")
def projects_list():
    """项目列表"""
    storage = JSONStorage()
    tasks = storage.get_all()

    projects_dict = {}
    for task in tasks:
        for tag in task.tags:
            if tag not in projects_dict:
                projects_dict[tag] = {
                    "id": tag,
                    "name": tag,
                    "description": f'包含标签 "{tag}" 的所有任务',
                    "tasks": [],
                }
            projects_dict[tag]["tasks"].append(task)

    projects = []
    for tag, data in projects_dict.items():
        total = len(data["tasks"])
        completed = sum(1 for t in data["tasks"] if t.status == Status.DONE)
        completion_rate = round((completed / total * 100), 1) if total > 0 else 0

        projects.append(
            {
                "id": tag,
                "name": data["name"],
                "description": data["description"],
                "total_tasks": total,
                "completed_tasks": completed,
                "completion_rate": completion_rate,
            }
        )

    projects.sort(key=lambda x: x["total_tasks"], reverse=True)
    return render_template("projects.html", projects=projects)


@projects_bp.route("/<project_id>")
def project_detail(project_id):
    """项目详情"""
    storage = JSONStorage()
    tasks = storage.get_all()
    project_tasks = [t for t in tasks if project_id in t.tags]

    if not project_tasks:
        return redirect(url_for("projects.projects_list"))

    total = len(project_tasks)
    completed = sum(1 for t in project_tasks if t.status == Status.DONE)
    completion_rate = round((completed / total * 100), 1) if total > 0 else 0

    return render_template(
        "project_detail.html",
        project_name=project_id,
        tasks=project_tasks,
        total=total,
        completed=completed,
        completion_rate=completion_rate,
    )
