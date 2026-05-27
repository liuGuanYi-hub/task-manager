"""周报路由"""
from flask import Blueprint, render_template, request
from storage.json_storage import JSONStorage
from models.task import Status
from datetime import datetime, timedelta
from urllib.parse import parse_qs

weekly_bp = Blueprint("weekly", __name__, url_prefix="/stats/weekly")


@weekly_bp.route("/")
def weekly_report():
    """周报页面"""
    storage = JSONStorage()
    tasks = storage.get_all()

    params = parse_qs(request.query_string.decode())
    current_date = datetime.fromisoformat(params["date"][0]) if "date" in params else datetime.now()

    week_start = current_date - timedelta(days=current_date.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)

    week_tasks = [t for t in tasks if week_start <= t.created_at <= week_end]
    completed_tasks = [t for t in week_tasks if t.status == Status.DONE]

    total_created = len(week_tasks)
    total_completed = len(completed_tasks)
    completion_rate = round((total_completed / total_created * 100), 1) if total_created > 0 else 0
    active_days = len(set(t.created_at.date() for t in week_tasks))

    daily_labels = []
    daily_data = []
    for i in range(7):
        day = week_start + timedelta(days=i)
        daily_labels.append(day.strftime("%m-%d"))
        daily_data.append(sum(1 for t in week_tasks if t.created_at.date() == day.date()))

    prev_week = (week_start - timedelta(days=7)).date().isoformat()
    next_week_date = week_start + timedelta(days=7)
    next_week = next_week_date.date().isoformat() if next_week_date <= datetime.now() else None

    return render_template(
        "weekly.html",
        week_start=week_start.strftime("%Y-%m-%d"),
        week_end=week_end.strftime("%Y-%m-%d"),
        total_created=total_created,
        total_completed=total_completed,
        completion_rate=completion_rate,
        active_days=active_days,
        daily_labels=daily_labels,
        daily_data=daily_data,
        completed_tasks=completed_tasks,
        created_tasks=week_tasks,
        prev_week=prev_week,
        next_week=next_week,
    )
