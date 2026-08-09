"""基于现有截止日期的提醒中心路由。"""

from datetime import datetime, timedelta

from flask import Blueprint, render_template, url_for

from models.task import Priority, Status, Task
from storage.factory import create_storage as JSONStorage


reminders_bp = Blueprint("reminders", __name__, url_prefix="/reminders")

_ACTIVE_STATUSES = [Status.TODO.value, Status.IN_PROGRESS.value]
_REMINDER_WINDOW_DAYS = 3


def _priority_class(priority: Priority) -> str:
    return {
        Priority.HIGH: "high",
        Priority.MEDIUM: "medium",
        Priority.LOW: "low",
    }[priority]


def _due_text(due_date: datetime, now: datetime) -> str:
    if due_date.date() == now.date():
        return f"今天 {due_date.strftime('%H:%M')}"
    if due_date.date() == (now + timedelta(days=1)).date():
        return f"明天 {due_date.strftime('%H:%M')}"
    return due_date.strftime("%m月%d日 %H:%M")


def _task_view(task: Task, project_names: dict[int, str], now: datetime, section_title: str) -> dict:
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description or "暂无描述",
        "priority": f"{task.priority.value}优先级",
        "priority_value": task.priority.value,
        "priority_class": _priority_class(task.priority),
        "meta": _due_text(task.due_date, now),
        "due_date": task.due_date.strftime("%Y-%m-%dT%H:%M") if task.due_date else "",
        "tag": task.tags[0] if task.tags else "未分类",
        "tags": ", ".join(task.tags),
        "project_id": str(task.project_id) if task.project_id is not None else "",
        "project": project_names.get(task.project_id, "未归属项目"),
        "status": task.status.value,
        "updated": task.updated_at.strftime("%Y-%m-%d %H:%M"),
        "context": section_title,
        "edit_url": url_for("edit_task", task_id=task.id),
        "update_url": url_for("update_task", task_id=task.id, next="/reminders/"),
        "toggle_url": url_for("toggle_task", task_id=task.id, next="/reminders/"),
    }


@reminders_bp.route("")
@reminders_bp.route("/")
def reminders_page():
    """显示未完成任务的逾期和临近截止提醒。"""
    now = datetime.now()
    deadline = now + timedelta(days=_REMINDER_WINDOW_DAYS)
    storage = JSONStorage()
    projects = storage.get_projects()
    project_names = {project.id: project.name for project in projects}

    overdue_tasks = storage.query(
        statuses=_ACTIVE_STATUSES,
        due_date_to=now - timedelta(microseconds=1),
        sort_by="due_date",
    )
    due_soon_tasks = storage.query(
        statuses=_ACTIVE_STATUSES,
        due_date_from=now,
        due_date_to=deadline,
        sort_by="due_date",
    )

    sections = [
        {
            "key": "overdue",
            "eyebrow": "OVERDUE",
            "title": "已逾期",
            "subtitle": "先处理仍未完成的截止事项",
            "accent": "rose",
            "tasks": [_task_view(task, project_names, now, "提醒中心 · 已逾期") for task in overdue_tasks],
        },
        {
            "key": "due-soon",
            "eyebrow": "NEXT 3 DAYS",
            "title": "未来 3 天",
            "subtitle": "提前安排即将到期的任务",
            "accent": "blue",
            "tasks": [_task_view(task, project_names, now, "提醒中心 · 未来 3 天") for task in due_soon_tasks],
        },
    ]
    return render_template(
        "reminders.html",
        sections=sections,
        overdue_total=len(overdue_tasks),
        due_soon_total=len(due_soon_tasks),
        total=len(overdue_tasks) + len(due_soon_tasks),
        window_days=_REMINDER_WINDOW_DAYS,
        projects=projects,
    )
