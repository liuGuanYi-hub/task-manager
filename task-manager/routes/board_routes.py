"""WeKan 风格看板路由。"""
from typing import Optional

from flask import Blueprint, render_template, request, redirect, url_for

from models.task import Status
from storage.json_storage import ANY_PROJECT
from storage.factory import create_storage as JSONStorage


board_bp = Blueprint("board", __name__, url_prefix="/board")

BOARD_COLUMNS = (
    {
        "key": Status.TODO,
        "label": "待办",
        "subtitle": "还没有开始的工作",
        "icon": "○",
        "accent": "todo",
    },
    {
        "key": Status.IN_PROGRESS,
        "label": "进行中",
        "subtitle": "正在推进的工作",
        "icon": "◐",
        "accent": "progress",
    },
    {
        "key": Status.DONE,
        "label": "已完成",
        "subtitle": "已经交付的工作",
        "icon": "✓",
        "accent": "done",
    },
)


def parse_project_filter(raw_value: Optional[str]):
    """将看板筛选参数解析为任意项目、未归属或具体项目 ID。"""
    if raw_value in (None, "", "all"):
        return ANY_PROJECT
    if raw_value == "none":
        return None
    try:
        return int(raw_value)
    except (TypeError, ValueError) as exc:
        raise ValueError("项目筛选参数无效") from exc


def project_filter_key(project_id) -> str:
    """将内部项目筛选值转换为 URL 参数。"""
    if project_id is ANY_PROJECT:
        return "all"
    if project_id is None:
        return "none"
    return str(project_id)


@board_bp.route("")
@board_bp.route("/")
def board_view():
    """显示按任务状态分列的看板。"""
    try:
        selected_project_id = parse_project_filter(request.args.get("project_id"))
    except ValueError:
        return "项目筛选参数无效", 400

    storage = JSONStorage()
    if selected_project_id is not ANY_PROJECT and selected_project_id is not None:
        if storage.get_project_by_id(selected_project_id) is None:
            return "项目不存在", 404

    tasks = storage.query(project_id=selected_project_id, sort_by="updated_at", reverse=True)
    tasks_by_status = {column["key"]: [] for column in BOARD_COLUMNS}
    for task in tasks:
        tasks_by_status[task.status].append(task)

    columns = []
    for column in BOARD_COLUMNS:
        column_data = dict(column)
        column_data["tasks"] = tasks_by_status[column["key"]]
        column_data["count"] = len(column_data["tasks"])
        columns.append(column_data)

    selected_project = (
        storage.get_project_by_id(selected_project_id)
        if selected_project_id is not ANY_PROJECT and selected_project_id is not None
        else None
    )
    return render_template(
        "board.html",
        columns=columns,
        projects=storage.get_projects(),
        selected_project=selected_project,
        project_filter_key=project_filter_key(selected_project_id),
        total_tasks=len(tasks),
    )


@board_bp.route("/task/<int:task_id>/status", methods=["POST"])
def update_board_status(task_id: int):
    """从看板卡片更新任务状态并持久化。"""
    try:
        selected_project_id = parse_project_filter(request.args.get("project_id"))
    except ValueError:
        return "项目筛选参数无效", 400

    try:
        new_status = Status(request.form.get("status", ""))
    except ValueError:
        return "任务状态无效", 400

    storage = JSONStorage()
    task = storage.get_by_id(task_id)
    if task is None or task.archived:
        return "任务不存在", 404
    if selected_project_id is not ANY_PROJECT and task.project_id != selected_project_id:
        return "任务不属于当前项目", 404

    task.status = new_status
    storage.update(task)
    return redirect(url_for("board.board_view", project_id=project_filter_key(selected_project_id)))
