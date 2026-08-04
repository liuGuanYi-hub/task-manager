"""保存筛选视图路由。"""
from datetime import datetime, timedelta
from typing import Any, Dict

from flask import Blueprint, redirect, render_template, request, url_for

from models.saved_view import SavedView
from models.task import Priority, Status, parse_datetime
from storage.json_storage import JSONStorage


views_bp = Blueprint("views", __name__, url_prefix="/views")

SORT_OPTIONS = {
    "created_at": "创建时间",
    "due_date": "截止时间",
    "updated_at": "更新时间",
    "title": "标题",
}
VALID_STATUSES = {status.value for status in Status}
VALID_PRIORITIES = {priority.value for priority in Priority}


def _source_values(source: Any, key: str) -> list:
    """兼容 Flask MultiDict 和 JSON 字典的多值读取。"""
    if hasattr(source, "getlist"):
        return source.getlist(key)
    value = source.get(key, [])
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value] if value not in (None, "") else []


def _normalize_date(value: Any) -> str:
    """校验并标准化日期输入。"""
    if value in (None, ""):
        return ""
    text = str(value).strip()
    try:
        parsed = parse_datetime(text)
    except ValueError as exc:
        raise ValueError(f"日期格式无效：{value}") from exc
    if parsed is None:
        return ""
    return parsed.date().isoformat() if len(text) == 10 else parsed.isoformat()


def normalize_filters(source: Any) -> Dict[str, Any]:
    """从查询参数或表单构造可持久化的筛选条件。"""
    project_raw = str(source.get("project_id", "all") or "all").strip()
    if project_raw in {"", "all", "none"}:
        project_id: Any = "all" if project_raw != "none" else "none"
    else:
        try:
            project_id = int(project_raw)
        except ValueError as exc:
            raise ValueError("项目筛选参数无效") from exc

    statuses: list = []
    for value in _source_values(source, "statuses"):
        statuses.extend(str(value).split(","))
    statuses = [status.strip() for status in statuses if str(status).strip()]
    invalid_statuses = set(statuses) - VALID_STATUSES
    if invalid_statuses:
        raise ValueError("任务状态筛选参数无效")

    priority = str(source.get("priority", "") or "").strip()
    if priority and priority not in VALID_PRIORITIES:
        raise ValueError("任务优先级筛选参数无效")

    sort_by = str(source.get("sort_by", "created_at") or "created_at").strip()
    if sort_by not in SORT_OPTIONS:
        raise ValueError("排序字段无效")

    reverse_raw = str(source.get("reverse", "") or "").lower()
    reverse = reverse_raw in {"1", "true", "yes", "on"}
    return {
        "project_id": project_id,
        "statuses": statuses,
        "priority": priority,
        "tag": str(source.get("tag", "") or "").strip(),
        "due_start": _normalize_date(source.get("due_start", "")),
        "due_end": _normalize_date(source.get("due_end", "")),
        "sort_by": sort_by,
        "reverse": reverse,
        "include_archived": False,
    }


def apply_preset(filters: Dict[str, Any], preset: str) -> Dict[str, Any]:
    """应用常用筛选预设。"""
    result = dict(filters)
    if preset == "high-incomplete":
        result["priority"] = Priority.HIGH.value
        result["statuses"] = [Status.TODO.value, Status.IN_PROGRESS.value]
    elif preset == "week-due":
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        result["due_start"] = week_start.date().isoformat()
        result["due_end"] = week_end.date().isoformat()
    elif preset:
        raise ValueError("筛选预设无效")
    return result


def _validate_project(storage: JSONStorage, filters: Dict[str, Any]) -> None:
    """校验保存视图引用的项目。"""
    project_id = filters.get("project_id")
    if isinstance(project_id, int) and storage.get_project_by_id(project_id) is None:
        raise LookupError("项目不存在")


def _view_for_query(filters: Dict[str, Any]) -> SavedView:
    return SavedView(name="当前筛选", filters=filters)


def _render_views(storage: JSONStorage, filters: Dict[str, Any], selected_view=None):
    _validate_project(storage, filters)
    tasks = storage.query_saved_view(_view_for_query(filters))
    project_id = filters.get("project_id")
    selected_project = storage.get_project_by_id(project_id) if isinstance(project_id, int) else None
    return render_template(
        "views.html",
        tasks=tasks,
        filters=filters,
        projects=storage.get_projects(),
        saved_views=storage.get_saved_views(),
        selected_view=selected_view,
        selected_project=selected_project,
        sort_options=SORT_OPTIONS,
    )


@views_bp.route("")
@views_bp.route("/")
def views_page():
    """显示临时筛选结果和保存视图列表。"""
    try:
        filters = normalize_filters(request.args)
        filters = apply_preset(filters, request.args.get("preset", ""))
        return _render_views(JSONStorage(), filters)
    except LookupError as exc:
        return str(exc), 404
    except ValueError as exc:
        return str(exc), 400


@views_bp.route("/<int:view_id>")
def saved_view_detail(view_id: int):
    """读取保存视图。"""
    storage = JSONStorage()
    view = storage.get_saved_view_by_id(view_id)
    if view is None:
        return "保存视图不存在", 404
    try:
        filters = normalize_filters(view.filters)
        return _render_views(storage, filters, selected_view=view)
    except LookupError as exc:
        return str(exc), 404
    except ValueError as exc:
        return str(exc), 400


@views_bp.route("/save", methods=["POST"])
def save_view():
    """保存当前筛选条件。"""
    name = request.form.get("name", "").strip()
    if not name:
        return "视图名称不能为空", 400
    try:
        filters = normalize_filters(request.form)
        storage = JSONStorage()
        _validate_project(storage, filters)
    except LookupError as exc:
        return str(exc), 404
    except ValueError as exc:
        return str(exc), 400

    view = storage.add_saved_view(SavedView(name=name, filters=filters))
    return redirect(url_for("views.saved_view_detail", view_id=view.id))


@views_bp.route("/<int:view_id>/delete", methods=["POST"])
def delete_saved_view(view_id: int):
    """删除保存视图。"""
    storage = JSONStorage()
    if not storage.delete_saved_view(view_id):
        return "保存视图不存在", 404
    return redirect(url_for("views.views_page"))
