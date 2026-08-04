"""日历视图路由"""
from flask import Blueprint, render_template, request
from storage.factory import create_storage as JSONStorage
from models.task import Task, parse_datetime
from datetime import date, datetime
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


@calendar_bp.route("/")
def calendar_view():
    """日历视图"""
    storage = JSONStorage()
    tasks = storage.get_all()

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
                "title": t.title,
                "description": t.description,
                "priority": t.priority.value,
                "priority_icon": "🔴" if t.priority.value == "高" else "🟡" if t.priority.value == "中" else "🟢",
                "status": t.status.value,
                "status_icon": "✅" if t.status.value == "已完成" else "🔄" if t.status.value == "进行中" else "⬜",
                "status_class": "done" if t.status.value == "已完成" else "",
            }
            for t in day_tasks
        ]

    return render_template(
        "calendar.html",
        month_title=month_title,
        days=days,
        today=datetime.now().isoformat(),
        tasks_json=tasks_json,
    )
