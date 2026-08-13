"""日历视图路由"""
from flask import Blueprint, jsonify, redirect, render_template, request, url_for
from storage.factory import create_storage as JSONStorage
from models.task import Task, parse_datetime
from datetime import date, datetime, timedelta
from calendar import monthrange
from typing import List
from urllib.parse import parse_qs

calendar_bp = Blueprint("calendar", __name__, url_prefix="/calendar")


def get_tasks_for_date(tasks: List[Task], target_date: date) -> List[Task]:
    """按截止日期获取日历任务，而不是按创建日期重复展示。"""
    return [
        task for task in tasks
        if not task.archived and task.due_date and task.due_date.date() == target_date
    ]


def _week_task_payload(task: Task, project_names: dict[int, str], date_value: date) -> dict:
    """把周视图任务转换为详情抽屉可复用的 data 属性。"""
    return {
        "id": task.id,
        "action_url": url_for("task_actions.task_action", task_id=task.id),
        "title": task.title,
        "description": task.description or "暂无描述",
        "priority": task.priority.value,
        "priority_value": task.priority.value,
        "priority_class": "high" if task.priority.value == "高" else "medium" if task.priority.value == "中" else "low",
        "status": task.status.value,
        "status_class": "done" if task.status.value == "已完成" else "",
        "due_date": task.due_date.strftime("%Y-%m-%dT%H:%M") if task.due_date else "",
        "meta": task.due_date.strftime("%m月%d日 %H:%M") if task.due_date else "暂无截止日期",
        "tag": task.tags[0] if task.tags else "未分类",
        "tags": ", ".join(task.tags),
        "project_id": str(task.project_id) if task.project_id is not None else "",
        "project": project_names.get(task.project_id, "未归属项目"),
        "updated": task.updated_at.strftime("%Y-%m-%d %H:%M"),
        "edit_url": url_for("edit_task", task_id=task.id),
        "update_url": url_for("update_task", task_id=task.id, next="/calendar/week"),
        "reschedule_url": url_for("calendar.reschedule_task", task_id=task.id),
        "context": f"{date_value.strftime('%Y年%m月%d日')} 周视图",
    }


@calendar_bp.route("/")
def calendar_view():
    """日历视图"""
    storage = JSONStorage()
    tasks = storage.get_all()
    projects = storage.get_projects()
    project_names = {project.id: project.name for project in projects}

    params = parse_qs(request.query_string.decode())
    current_date = datetime.now()
    if "date" in params:
        try:
            current_date = parse_datetime(params["date"][0], current_date) or current_date
        except ValueError:
            pass

    year = current_date.year
    month = current_date.month
    first_weekday, days_in_month = monthrange(year, month)
    first_weekday = (first_weekday - 1) % 7
    month_title = current_date.strftime("%Y年%m月")

    days = [{"is_empty": True} for _ in range(first_weekday)]
    today = datetime.now().date()

    for day in range(1, days_in_month + 1):
        date = datetime(year, month, day)
        day_tasks = get_tasks_for_date(tasks, date.date())
        priorities = [
            "high" if task.priority.value == "高" else "medium" if task.priority.value == "中" else "low"
            for task in day_tasks
        ]
        days.append(
            {
                "is_empty": False,
                "day": day,
                "date": date.strftime("%Y-%m-%d"),
                "is_today": date.date() == today,
                "task_count": len(day_tasks),
                "priorities": priorities,
            }
        )

    tasks_json = {}
    for day in days:
        if day.get("is_empty"):
            continue

        date_str = day["date"]
        date_value = datetime.fromisoformat(date_str).date()
        day_tasks = get_tasks_for_date(tasks, date_value)
        tasks_json[date_str] = [
            {
                "id": t.id,
                "action_url": url_for("task_actions.task_action", task_id=t.id),
                "title": t.title,
                "description": t.description or "暂无描述",
                "priority": t.priority.value,
                "priority_value": t.priority.value,
                "priority_class": "high" if t.priority.value == "高" else "medium" if t.priority.value == "中" else "low",
                "priority_icon": "🔴" if t.priority.value == "高" else "🟡" if t.priority.value == "中" else "🟢",
                "status": t.status.value,
                "status_icon": "✅" if t.status.value == "已完成" else "🔄" if t.status.value == "进行中" else "⬜",
                "status_class": "done" if t.status.value == "已完成" else "",
                "due_date": t.due_date.strftime("%Y-%m-%dT%H:%M") if t.due_date else "",
                "meta": t.due_date.strftime("%m月%d日 %H:%M") if t.due_date else "暂无截止日期",
                "tag": t.tags[0] if t.tags else "未分类",
                "tags": ", ".join(t.tags),
                "project_id": str(t.project_id) if t.project_id is not None else "",
                "project": project_names.get(t.project_id, "未归属项目"),
                "updated": t.updated_at.strftime("%Y-%m-%d %H:%M"),
                "edit_url": url_for("edit_task", task_id=t.id),
                "update_url": url_for("update_task", task_id=t.id, next="/calendar/"),
                "reschedule_url": url_for("calendar.reschedule_task", task_id=t.id),
                "context": f"{date_value.strftime('%Y年%m月%d日')} 日历",
            }
            for t in day_tasks
        ]

    return render_template(
        "calendar.html",
        month_title=month_title,
        days=days,
        today=datetime.now().isoformat(),
        tasks_json=tasks_json,
        projects=projects,
    )


def _calendar_wants_json() -> bool:
    """识别拖拽改期请求是否需要机器可读响应。"""
    return request.is_json or "application/json" in request.headers.get("Accept", "")


@calendar_bp.route("/task/<int:task_id>/reschedule", methods=["POST"])
def reschedule_task(task_id: int):
    """只修改任务截止日期的轻量改期接口，保留原有截止时间。"""
    storage = JSONStorage()
    task = storage.get_by_id(task_id)
    if task is None or task.archived:
        if _calendar_wants_json():
            return jsonify({"error": {"code": "task_not_found", "message": "任务不存在或已归档"}}), 404
        return "任务不存在或已归档", 404

    data = request.get_json(silent=True) if request.is_json else request.form
    data = data if data is not None and hasattr(data, "get") else {}
    target_raw = str(data.get("date", "")).strip()
    try:
        target_date = date.fromisoformat(target_raw)
    except ValueError:
        if _calendar_wants_json():
            return jsonify({"error": {"code": "invalid_date", "message": "目标日期格式无效"}}), 400
        return "目标日期格式无效", 400

    original_time = task.due_date.time() if task.due_date else datetime.min.time()
    task.due_date = datetime.combine(target_date, original_time)
    if not storage.update(task):
        if _calendar_wants_json():
            return jsonify({"error": {"code": "update_failed", "message": "任务改期失败"}}), 500
        return "任务改期失败", 500

    if _calendar_wants_json():
        return jsonify(
            {
                "data": {
                    "id": task.id,
                    "due_date": task.due_date.isoformat(),
                }
            }
        )

    next_url = data.get("next") or request.args.get("next")
    if next_url and next_url.startswith("/") and not next_url.startswith("//"):
        return redirect(next_url)
    return redirect(url_for("calendar.calendar_view"))


@calendar_bp.route("/week")
def calendar_week_view():
    """按任务截止日期展示当前周的 7 天工作安排。"""
    storage = JSONStorage()
    tasks = storage.get_all()
    projects = storage.get_projects()
    project_names = {project.id: project.name for project in projects}

    params = parse_qs(request.query_string.decode())
    current_date = datetime.now()
    if "date" in params:
        try:
            current_date = parse_datetime(params["date"][0], current_date) or current_date
        except ValueError:
            pass

    week_start = (current_date - timedelta(days=current_date.weekday())).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    today = datetime.now().date()
    week_days = []
    weekday_labels = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    for offset, label in enumerate(weekday_labels):
        day_value = (week_start + timedelta(days=offset)).date()
        day_tasks = get_tasks_for_date(tasks, day_value)
        week_days.append(
            {
                "label": label,
                "date": day_value.isoformat(),
                "title": day_value.strftime("%m月%d日"),
                "is_today": day_value == today,
                "tasks": [
                    _week_task_payload(task, project_names, day_value)
                    for task in day_tasks
                ],
            }
        )

    week_start_value = week_start.date()
    previous_week = (week_start_value - timedelta(days=7)).isoformat()
    next_week = (week_start_value + timedelta(days=7)).isoformat()
    week_end_value = week_start_value + timedelta(days=6)

    return render_template(
        "calendar_week.html",
        week_title=f"{week_start_value.strftime('%Y年%m月%d日')} - {week_end_value.strftime('%m月%d日')}",
        week_start=week_start_value.isoformat(),
        previous_week=previous_week,
        next_week=next_week,
        week_days=week_days,
        projects=projects,
    )
