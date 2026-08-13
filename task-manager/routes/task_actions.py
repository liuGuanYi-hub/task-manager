"""统一任务快速操作路由。"""

from datetime import date, datetime, time, timedelta

from flask import Blueprint, jsonify, redirect, request, url_for

from models.task import Status, parse_datetime
from storage.factory import create_storage as JSONStorage


task_actions_bp = Blueprint("task_actions", __name__, url_prefix="/task")


def _wants_json() -> bool:
    return request.is_json or "application/json" in request.headers.get("Accept", "")


def _payload():
    data = request.get_json(silent=True) if request.is_json else request.form
    return data if data is not None and hasattr(data, "get") else {}


def _safe_next(data) -> str:
    next_url = str(data.get("next", "") or request.args.get("next", "")).strip()
    if next_url.startswith("/") and not next_url.startswith("//"):
        return next_url
    return url_for("index")


def _task_data(task):
    return {
        "id": task.id,
        "title": task.title,
        "status": task.status.value,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "project_id": task.project_id,
        "archived": task.archived,
    }


def _error(message: str, code: str, status: int):
    if _wants_json():
        return jsonify({"error": {"code": code, "message": message}}), status
    return message, status


def _tomorrow_due_date(task) -> datetime:
    """将任务安排到明天，保留已有时间；无时间的任务使用 09:00。"""
    task_time = task.due_date.time() if task.due_date else time(9, 0)
    return datetime.combine(date.today() + timedelta(days=1), task_time)


@task_actions_bp.route("/<int:task_id>/action", methods=["POST"])
def task_action(task_id: int):
    """执行完成、恢复、归档或延后，并统一返回反馈。"""
    storage = JSONStorage()
    task = storage.get_by_id(task_id)
    if task is None or task.archived:
        return _error("任务不存在或已归档", "task_not_found", 404)

    data = _payload()
    action = str(data.get("action", "") or "").strip().lower()
    if action == "complete":
        task.status = Status.DONE
        message = "任务已完成"
    elif action in {"reopen", "toggle"}:
        task.status = Status.TODO if action == "reopen" or task.status == Status.DONE else Status.DONE
        message = "任务已恢复为待办" if task.status == Status.TODO else "任务已完成"
    elif action == "archive":
        if not storage.archive(task_id):
            return _error("任务归档失败", "archive_failed", 500)
        message = "任务已归档"
    elif action == "delay":
        raw_due_date = str(data.get("due_date", "") or "").strip()
        if raw_due_date:
            try:
                task.due_date = parse_datetime(raw_due_date)
            except ValueError:
                return _error("延后日期格式无效", "invalid_due_date", 400)
        else:
            task.due_date = _tomorrow_due_date(task)
        message = "任务已延后到明天" if not raw_due_date else "任务已改期"
    else:
        return _error("任务动作无效", "invalid_action", 400)

    if action != "archive" and not storage.update(task):
        return _error("任务更新失败", "update_failed", 500)

    next_url = _safe_next(data)
    if _wants_json():
        return jsonify({"data": {"action": action, "message": message, "task": _task_data(task), "next": next_url}})
    return redirect(next_url)
