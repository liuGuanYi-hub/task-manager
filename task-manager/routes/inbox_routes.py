"""Inbox 收集箱与任务分流路由。"""

from datetime import date, datetime

from flask import Blueprint, redirect, render_template, request, url_for

from models.task import Status, parse_datetime
from storage.factory import create_storage as JSONStorage


inbox_bp = Blueprint("inbox", __name__, url_prefix="/inbox")


def _inbox_redirect(feedback: str = ""):
    """返回 Inbox，并将一次性操作反馈放入查询参数。"""
    if feedback:
        return redirect(url_for("inbox.inbox_page", feedback=feedback))
    return redirect(url_for("inbox.inbox_page"))


def _unplanned_tasks(storage):
    """Inbox 只显示未归档且没有截止日期的任务。"""
    tasks = storage.query(sort_by="updated_at", reverse=True)
    return [task for task in tasks if task.due_date is None]


@inbox_bp.route("")
@inbox_bp.route("/")
def inbox_page():
    """显示收集箱，并提供任务分流入口。"""
    storage = JSONStorage()
    tasks = _unplanned_tasks(storage)
    projects = storage.get_projects()
    project_names = {project.id: project.name for project in projects}
    return render_template(
        "inbox.html",
        tasks=tasks,
        projects=projects,
        project_names=project_names,
        inbox_count=len(tasks),
        projectless_count=sum(1 for task in tasks if task.project_id is None),
        tagged_count=sum(1 for task in tasks if task.tags),
        current_date=date.today().isoformat(),
        feedback=request.args.get("feedback", "").strip(),
    )


@inbox_bp.route("/task/<int:task_id>/schedule", methods=["POST"])
def schedule_task(task_id: int):
    """把 Inbox 任务安排到今天、指定日期或项目。"""
    storage = JSONStorage()
    task = storage.get_by_id(task_id)
    if task is None or task.archived:
        return "任务不存在", 404

    action = request.form.get("action", "").strip().lower()
    if action == "today":
        task.due_date = datetime.combine(date.today(), datetime.min.time())
        feedback = "任务已安排到今天"
    elif action == "date":
        raw_due_date = request.form.get("due_date", "").strip()
        try:
            due_date = parse_datetime(raw_due_date) if raw_due_date else None
        except ValueError:
            return "截止日期格式无效", 400
        if due_date is None:
            return "截止日期不能为空", 400
        task.due_date = due_date
        feedback = "任务已安排到指定日期"
    elif action == "project":
        raw_project_id = request.form.get("project_id", "").strip()
        try:
            project_id = int(raw_project_id)
        except (TypeError, ValueError):
            return "项目 ID 格式无效", 400
        project = storage.get_project_by_id(project_id)
        if project is None:
            return "项目不存在", 400
        task.project_id = project_id
        feedback = f"任务已归入项目：{project.name}，仍待安排日期"
    else:
        return "分流动作无效", 400

    if not storage.update(task):
        return "任务更新失败", 500
    return _inbox_redirect(feedback)


@inbox_bp.route("/task/<int:task_id>/toggle", methods=["POST"])
def toggle_inbox_task(task_id: int):
    """在 Inbox 内快速完成或恢复任务。"""
    storage = JSONStorage()
    task = storage.get_by_id(task_id)
    if task is None or task.archived:
        return "任务不存在", 404
    task.status = Status.TODO if task.status == Status.DONE else Status.DONE
    if not storage.update(task):
        return "任务更新失败", 500
    return _inbox_redirect("任务状态已更新")


@inbox_bp.route("/task/<int:task_id>/archive", methods=["POST"])
def archive_inbox_task(task_id: int):
    """在 Inbox 内快速归档任务。"""
    storage = JSONStorage()
    if not storage.archive(task_id):
        return "任务不存在", 404
    return _inbox_redirect("任务已归档")
