"""Today 工作台路由。"""

from datetime import date, datetime, timedelta

from flask import Blueprint, render_template

from models.task import Priority, Status, Task
from storage.factory import create_storage as JSONStorage


today_bp = Blueprint("today", __name__, url_prefix="/today")

_WEEKDAYS = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]


def _priority_class(priority: Priority) -> str:
    return {
        Priority.HIGH: "high",
        Priority.MEDIUM: "medium",
        Priority.LOW: "low",
    }[priority]


def _format_due_date(due_date: datetime | None, current_date: date) -> str:
    """将任务截止时间转换成适合 Today 卡片阅读的短文本。"""
    if due_date is None:
        return "暂无截止日期"

    due_day = due_date.date()
    if due_day < current_date:
        return f"逾期 {(current_date - due_day).days} 天"

    time_suffix = due_date.strftime(" %H:%M") if due_date.time() != datetime.min.time() else ""
    if due_day == current_date:
        return f"今天{time_suffix}"
    if due_day == current_date + timedelta(days=1):
        return f"明天{time_suffix}"
    if due_day == current_date + timedelta(days=2):
        return f"后天{time_suffix}"
    return due_date.strftime("%m月%d日") + time_suffix


def _format_updated(updated_at: datetime | None) -> str:
    if updated_at is None:
        return "暂无更新时间"
    return updated_at.strftime("%Y-%m-%d %H:%M")


def _task_view(task: Task, project_names: dict[int, str], current_date: date, section_title: str) -> dict:
    """把领域模型映射为 Today 模板需要的展示数据。"""
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description or "暂无描述",
        "priority": f"{task.priority.value}优先级",
        "priority_value": task.priority.value,
        "priority_class": _priority_class(task.priority),
        "meta": _format_due_date(task.due_date, current_date),
        "due_date_value": task.due_date.strftime("%Y-%m-%dT%H:%M") if task.due_date else "",
        "tag": task.tags[0] if task.tags else "未分类",
        "tags_value": ", ".join(task.tags),
        "project_id": str(task.project_id) if task.project_id is not None else "",
        "project": project_names.get(task.project_id, "未归属项目"),
        "status": task.status.value,
        "completed": task.status == Status.DONE,
        "updated": _format_updated(task.updated_at),
        "context": section_title,
    }


def _build_sections(tasks: list[Task], projects, current_date: date) -> list[dict]:
    """按截止日期把未归档任务分组，保持 Today 的四段式工作台结构。"""
    project_names = {project.id: project.name for project in projects}
    grouped = {"today": [], "overdue": [], "upcoming": [], "someday": []}

    for task in tasks:
        if task.due_date is None:
            section_key = "someday"
        elif task.due_date.date() == current_date:
            section_key = "today"
        elif task.due_date.date() < current_date:
            if task.status == Status.DONE:
                continue
            section_key = "overdue"
        else:
            section_key = "upcoming"

        grouped[section_key].append(task)

    section_meta = [
        (
            "today",
            "TODAY",
            "今天要做",
            "把注意力放在当前最重要的事情上",
            "blue",
        ),
        (
            "overdue",
            "OVERDUE",
            "已逾期",
            "先处理仍未完成的逾期任务",
            "rose",
        ),
        (
            "upcoming",
            "UPCOMING",
            "接下来",
            "提前看看未来安排，给后续工作留出空间",
            "mint",
        ),
        (
            "someday",
            "NO DATE",
            "还没有安排日期",
            "先收集，等准备好再安排时间",
            "violet",
        ),
    ]

    sections = []
    for key, eyebrow, title, subtitle, accent in section_meta:
        section_tasks = [
            _task_view(task, project_names, current_date, title)
            for task in grouped[key]
        ]
        sections.append(
            {
                "key": key,
                "eyebrow": eyebrow,
                "title": title,
                "subtitle": subtitle,
                "count": len(section_tasks),
                "accent": accent,
                "tasks": section_tasks,
            }
        )
    return sections


def _today_metrics(sections: list[dict]) -> dict:
    section_by_key = {section["key"]: section for section in sections}
    today_tasks = section_by_key["today"]["tasks"]
    today_total = len(today_tasks)
    today_done = sum(1 for task in today_tasks if task["completed"])
    completion_rate = (today_done / today_total * 100) if today_total else 0
    return {
        "today_total": today_total,
        "today_done": today_done,
        "today_remaining": today_total - today_done,
        "overdue_total": section_by_key["overdue"]["count"],
        "upcoming_total": section_by_key["upcoming"]["count"],
        "someday_total": section_by_key["someday"]["count"],
        "completion_rate": completion_rate,
    }


@today_bp.route("")
@today_bp.route("/")
def today_page():
    """显示按真实任务数据聚合的 Today 工作台。"""
    current_date = date.today()
    storage = JSONStorage()
    tasks = storage.query(sort_by="due_date")
    sections = _build_sections(tasks, storage.get_projects(), current_date)
    return render_template(
        "today.html",
        current_date=current_date.strftime("%Y年%m月%d日"),
        current_weekday=_WEEKDAYS[current_date.weekday()],
        sections=sections,
        projects=storage.get_projects(),
        **_today_metrics(sections),
    )
