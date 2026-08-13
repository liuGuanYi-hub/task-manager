"""Agenda 日程与轻量时间线页面。"""

from datetime import date, datetime, time, timedelta

from flask import Blueprint, render_template, request, url_for

from models.task import Status
from storage.factory import create_storage as JSONStorage


agenda_bp = Blueprint("agenda", __name__, url_prefix="/agenda")

DATE_FILTERS = {
    "week": "七天时间线",
    "today": "选中日期",
    "overdue": "逾期任务",
    "unscheduled": "未安排任务",
}
DENSITY_FILTERS = {
    "all": "全部密度",
    "planned": "有任务的日子",
    "busy": "高密度（3 项以上）",
    "empty": "空白日",
}


def _priority_rank(task) -> int:
    return {"高": 0, "中": 1, "低": 2}.get(task.priority.value, 3)


def _sort_tasks(tasks):
    return sorted(
        tasks,
        key=lambda task: (
            task.due_date.time() if task.due_date else time.max,
            _priority_rank(task),
            task.title,
        ),
    )


def _task_item(task, project_names: dict[int, str], context: str):
    due_date = task.due_date
    return {
        "task": task,
        "action_url": url_for("task_actions.task_action", task_id=task.id),
        "meta": due_date.strftime("%m月%d日 %H:%M") if due_date else "尚未安排日期",
        "time_label": due_date.strftime("%H:%M") if due_date else "待安排",
        "priority_class": "high" if task.priority.value == "高" else "medium" if task.priority.value == "中" else "low",
        "project": project_names.get(task.project_id, "未归属项目"),
        "tag": task.tags[0] if task.tags else "未分类",
        "context": context,
        "edit_url": url_for("edit_task", task_id=task.id),
        "update_url": url_for("update_task", task_id=task.id, next="/agenda/"),
        "date": due_date.date().isoformat() if due_date else "",
        "reschedule_url": url_for("calendar.reschedule_task", task_id=task.id) if due_date else "",
    }


def _selected_date() -> date:
    raw_date = request.args.get("date", "").strip()
    if raw_date:
        try:
            return date.fromisoformat(raw_date[:10])
        except ValueError:
            pass
    return datetime.now().date()


@agenda_bp.route("/")
def agenda_view():
    """展示从选中日期开始的七天执行时间线。"""
    storage = JSONStorage()
    tasks = [task for task in storage.get_all() if not task.archived]
    projects = storage.get_projects()
    project_names = {project.id: project.name for project in projects}
    selected_date = _selected_date()
    today = datetime.now().date()

    all_day_groups = []
    for offset in range(7):
        day_value = selected_date + timedelta(days=offset)
        day_tasks = _sort_tasks(
            [task for task in tasks if task.due_date and task.due_date.date() == day_value]
        )
        density = "busy" if len(day_tasks) >= 3 else "planned" if day_tasks else "empty"
        all_day_groups.append(
            {
                "date": day_value.isoformat(),
                "label": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][day_value.weekday()],
                "title": day_value.strftime("%m月%d日"),
                "is_today": day_value == today,
                "density": density,
                "tasks": [
                    _task_item(task, project_names, f"{day_value.strftime('%Y年%m月%d日')} Agenda")
                    for task in day_tasks
                ],
            }
        )

    date_filter = request.args.get("date_filter", "week").strip().lower()
    if date_filter not in DATE_FILTERS:
        date_filter = "week"
    density_filter = request.args.get("density", "all").strip().lower()
    if density_filter not in DENSITY_FILTERS:
        density_filter = "all"

    if date_filter == "today":
        day_groups = [group for group in all_day_groups if group["date"] == selected_date.isoformat()]
    elif date_filter in {"overdue", "unscheduled"}:
        day_groups = []
    else:
        day_groups = list(all_day_groups)
    if density_filter != "all":
        day_groups = [group for group in day_groups if group["density"] == density_filter or (density_filter == "planned" and group["density"] == "busy")]

    overdue_tasks = _sort_tasks(
        [task for task in tasks if task.due_date and task.due_date.date() < selected_date and task.status != Status.DONE]
    )
    unscheduled_tasks = _sort_tasks(
        [task for task in tasks if task.due_date is None and task.status != Status.DONE]
    )
    planned_count = sum(len(group["tasks"]) for group in day_groups)
    completed_count = sum(
        1 for group in day_groups for item in group["tasks"] if item["task"].status == Status.DONE
    )
    range_end = selected_date + timedelta(days=6)

    return render_template(
        "agenda.html",
        active_page="agenda",
        selected_date=selected_date.isoformat(),
        today_date=today.isoformat(),
        previous_date=(selected_date - timedelta(days=7)).isoformat(),
        next_date=(selected_date + timedelta(days=7)).isoformat(),
        range_title=f"{selected_date.strftime('%Y年%m月%d日')} - {range_end.strftime('%m月%d日')}",
        day_groups=day_groups,
        overdue_tasks=[_task_item(task, project_names, "逾期任务") for task in overdue_tasks],
        unscheduled_tasks=[_task_item(task, project_names, "未安排任务") for task in unscheduled_tasks],
        planned_count=planned_count,
        completed_count=completed_count,
        overdue_count=len(overdue_tasks),
        date_filter=date_filter,
        date_filter_label=DATE_FILTERS[date_filter],
        density_filter=density_filter,
        density_filter_label=DENSITY_FILTERS[density_filter],
        show_overdue=date_filter in {"week", "overdue"},
        show_unscheduled=date_filter in {"week", "unscheduled"},
        projects=projects,
    )
