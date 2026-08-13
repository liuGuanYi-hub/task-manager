"""统一任务快速操作路由。"""

from datetime import date, datetime, time, timedelta
import json

from flask import Blueprint, jsonify, redirect, request, url_for

from models.task import Priority, Status, parse_datetime
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


def _task_snapshot(task):
    """提取可用于撤销和冲突检测的业务状态。"""
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "priority": task.priority.value,
        "status": task.status.value,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "project_id": task.project_id,
        "tags": list(task.tags),
        "archived": task.archived,
    }


def _restore_snapshot(task, snapshot):
    """将业务字段恢复到快照；更新时间由存储层统一维护。"""
    if not isinstance(snapshot, dict) or snapshot.get("id") != task.id:
        raise ValueError("撤销快照无效")
    task.title = str(snapshot.get("title", task.title))
    task.description = str(snapshot.get("description", ""))
    task.priority = Priority(str(snapshot.get("priority", task.priority.value)))
    task.status = Status(str(snapshot.get("status", task.status.value)))
    task.due_date = parse_datetime(snapshot.get("due_date"))
    task.completed_at = parse_datetime(snapshot.get("completed_at"))
    task.project_id = snapshot.get("project_id")
    task.tags = [str(tag).strip() for tag in snapshot.get("tags", []) if str(tag).strip()]
    task.archived = bool(snapshot.get("archived", False))


def _json_field(data, key):
    """兼容 JSON 请求体和 FormData 中的 JSON 字符串。"""
    value = data.get(key)
    if isinstance(value, dict):
        return value
    if value in (None, ""):
        return None
    try:
        parsed = json.loads(str(value))
    except (TypeError, json.JSONDecodeError):
        return None
    return parsed if isinstance(parsed, dict) else None


def _undo_task(storage, task, data):
    """按前一状态撤销动作，并拒绝覆盖撤销窗口期间的新修改。"""
    previous = _json_field(data, "snapshot")
    expected = _json_field(data, "expected")
    if previous is None or expected is None:
        return _error("撤销信息已失效，请刷新后重试", "invalid_undo", 400)
    current = _task_snapshot(task)
    if current != expected:
        return _error("任务状态已变化，无法撤销本次操作", "undo_conflict", 409)

    try:
        _restore_snapshot(task, previous)
        if not storage.update(task):
            _restore_snapshot(task, current)
            return _error("撤销失败，任务状态未改变", "undo_failed", 500)
    except Exception:
        _restore_snapshot(task, current)
        return _error("撤销失败，任务状态未改变", "undo_failed", 500)

    next_url = _safe_next(data)
    if _wants_json():
        return jsonify(
            {
                "data": {
                    "action": "undo",
                    "message": "已撤销上一步操作",
                    "task": _task_data(task),
                    "next": next_url,
                }
            }
        )
    return redirect(next_url)


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
    data = _payload()
    action = str(data.get("action", "") or "").strip().lower()
    if task is None or (task.archived and action != "undo"):
        return _error("任务不存在或已归档", "task_not_found", 404)
    if action == "undo":
        return _undo_task(storage, task, data)

    previous = _task_snapshot(task)
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

    try:
        if action != "archive" and not storage.update(task):
            _restore_snapshot(task, previous)
            return _error("任务更新失败，任务状态已恢复", "update_failed", 500)
    except Exception:
        _restore_snapshot(task, previous)
        return _error("任务更新失败，任务状态已恢复", "update_failed", 500)

    next_url = _safe_next(data)
    if _wants_json():
        return jsonify(
            {
                "data": {
                    "action": action,
                    "message": message,
                    "task": _task_data(task),
                    "next": next_url,
                    "undo": {
                        "snapshot": previous,
                        "expected": _task_snapshot(task),
                    },
                }
            }
        )
    return redirect(next_url)
