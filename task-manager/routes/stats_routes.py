"""统计路由"""
from flask import Blueprint, render_template
from storage.factory import create_storage as JSONStorage
from models.task import Status, Priority
from datetime import datetime, timedelta
from collections import Counter

stats_bp = Blueprint("stats", __name__, url_prefix="/stats")


@stats_bp.route("/")
def stats_dashboard():
    """统计仪表板"""
    storage = JSONStorage()
    tasks = storage.get_all()

    total = len(tasks)
    todo = sum(1 for t in tasks if t.status == Status.TODO)
    in_progress = sum(1 for t in tasks if t.status == Status.IN_PROGRESS)
    done = sum(1 for t in tasks if t.status == Status.DONE)
    completion_rate = round((done / total * 100), 1) if total > 0 else 0

    high_count = sum(1 for t in tasks if t.priority == Priority.HIGH)
    medium_count = sum(1 for t in tasks if t.priority == Priority.MEDIUM)
    low_count = sum(1 for t in tasks if t.priority == Priority.LOW)

    all_tags = []
    for task in tasks:
        all_tags.extend(task.tags)
    top_tags = Counter(all_tags).most_common(10)

    today = datetime.now()
    trend_data = []
    trend_labels = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        trend_labels.append(date.strftime("%m-%d"))
        trend_data.append(sum(1 for t in tasks if t.created_at.date() == date.date()))

    return render_template(
        "stats.html",
        total=total,
        todo=todo,
        in_progress=in_progress,
        done=done,
        completion_rate=completion_rate,
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count,
        top_tags=top_tags,
        trend_labels=trend_labels,
        trend_data=trend_data,
    )
