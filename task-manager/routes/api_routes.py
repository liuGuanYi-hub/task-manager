"""面向脚本和其他客户端的 REST API。"""

import hmac
import math
import os
from pathlib import Path
from typing import Any, Dict

from flask import Blueprint, jsonify, request

from models.project import Project
from models.task import Priority, Status, Task, parse_datetime
from storage.json_storage import ANY_PROJECT
from storage.factory import create_storage as JSONStorage


api_bp = Blueprint("api", __name__, url_prefix="/api/v1")
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
API_TOKEN_ENV = "TASK_MANAGER_API_TOKEN"


class ApiInputError(ValueError):
    """API 请求体或查询参数无效。"""

    code = "invalid_request"


def _error(message: str, status: int = 400, code: str = "invalid_request"):
    return jsonify({"error": {"code": code, "message": message}}), status


def _auth_error():
    response, status = _error("需要有效的 Bearer Token", 401, "authentication_required")
    response.headers["WWW-Authenticate"] = "Bearer"
    return response, status


@api_bp.before_request
def authenticate_api_request():
    """配置 API token 后保护除健康检查以外的所有 API。"""
    if request.endpoint == "api.health":
        return None

    configured_token = os.getenv(API_TOKEN_ENV, "").strip()
    if not configured_token:
        return None

    authorization = request.headers.get("Authorization", "")
    scheme, separator, supplied_token = authorization.partition(" ")
    if (
        not separator
        or scheme.lower() != "bearer"
        or not supplied_token
        or not hmac.compare_digest(supplied_token.strip(), configured_token)
    ):
        return _auth_error()
    return None


def _payload() -> Dict[str, Any]:
    value = request.get_json(silent=True)
    if not isinstance(value, dict):
        raise ApiInputError("请求体必须是 JSON 对象")
    return value


def _parse_project_id(value: Any, *, allow_none: bool = True):
    if value in (None, "", "none") and allow_none:
        return None
    if isinstance(value, bool):
        raise ApiInputError("project_id 必须是正整数或 null")
    try:
        project_id = int(value)
    except (TypeError, ValueError) as exc:
        raise ApiInputError("project_id 必须是正整数或 null") from exc
    if project_id <= 0:
        raise ApiInputError("project_id 必须是正整数")
    return project_id


def _parse_task_values(payload: Dict[str, Any], storage, *, partial: bool = False) -> Dict[str, Any]:
    values: Dict[str, Any] = {}
    if not partial or "title" in payload:
        title = payload.get("title")
        if not isinstance(title, str) or not title.strip():
            raise ApiInputError("title 不能为空")
        values["title"] = title.strip()

    if not partial or "description" in payload:
        description = payload.get("description", "")
        if not isinstance(description, str):
            raise ApiInputError("description 必须是字符串")
        values["description"] = description

    if not partial or "priority" in payload:
        try:
            values["priority"] = Priority(payload.get("priority", Priority.MEDIUM.value))
        except ValueError as exc:
            raise ApiInputError("priority 不是有效值") from exc

    if not partial or "status" in payload:
        try:
            values["status"] = Status(payload.get("status", Status.TODO.value))
        except ValueError as exc:
            raise ApiInputError("status 不是有效值") from exc

    if not partial or "due_date" in payload:
        try:
            values["due_date"] = parse_datetime(payload.get("due_date"))
        except ValueError as exc:
            raise ApiInputError("due_date 必须是 ISO 日期或日期时间") from exc

    if not partial or "tags" in payload:
        tags = payload.get("tags", [])
        if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
            raise ApiInputError("tags 必须是字符串数组")
        values["tags"] = [tag.strip() for tag in tags if tag.strip()]

    if not partial or "project_id" in payload:
        project_id = _parse_project_id(payload.get("project_id"))
        if project_id is not None and storage.get_project_by_id(project_id) is None:
            raise ApiInputError("project_id 对应的项目不存在")
        values["project_id"] = project_id

    return values


def _task_data(task: Task, storage) -> dict:
    data = task.to_dict()
    project = storage.get_project_by_id(task.project_id) if task.project_id else None
    data["project_name"] = project.name if project else None
    return data


def _project_data(project: Project, storage) -> dict:
    tasks = storage.get_all(project_id=project.id)
    result = project.to_dict()
    result["total_tasks"] = len(tasks)
    result["completed_tasks"] = sum(1 for task in tasks if task.status == Status.DONE)
    return result


def _pagination_args():
    """解析并限制集合接口的分页参数。"""
    try:
        page = int(request.args.get("page", "1"))
        page_size = int(request.args.get("page_size", str(DEFAULT_PAGE_SIZE)))
    except ValueError as exc:
        raise ApiInputError("page 和 page_size 必须是整数") from exc
    if page < 1:
        raise ApiInputError("page 必须大于等于 1")
    if page_size < 1 or page_size > MAX_PAGE_SIZE:
        raise ApiInputError(f"page_size 必须在 1 到 {MAX_PAGE_SIZE} 之间")
    return page, page_size


def _paginate(items, page: int, page_size: int):
    total = len(items)
    start = (page - 1) * page_size
    page_items = items[start : start + page_size]
    return page_items, {
        "page": page,
        "page_size": page_size,
        "pages": math.ceil(total / page_size) if total else 0,
        "total": total,
        "count": total,
        "returned": len(page_items),
    }


@api_bp.errorhandler(ApiInputError)
def handle_api_input_error(error):
    return _error(str(error))


@api_bp.route("/health")
def health():
    storage = JSONStorage()
    return jsonify(
        {
            "data": {
                "status": "ok",
                "backend": getattr(storage, "backend_name", "json"),
                "database": Path(storage.db_path).name,
            }
        }
    )


@api_bp.route("/tasks", methods=["GET"])
@api_bp.route("/tasks/", methods=["GET"])
def list_tasks_api():
    storage = JSONStorage()
    page, page_size = _pagination_args()
    project_raw = request.args.get("project_id")
    if project_raw in (None, "", "all"):
        project_id = ANY_PROJECT
    else:
        project_id = _parse_project_id(project_raw, allow_none=True)

    status_values = request.args.getlist("status")
    if not status_values and request.args.get("statuses"):
        status_values = request.args.get("statuses", "").split(",")
    status_values = [value.strip() for value in status_values if value.strip()]
    if set(status_values) - {status.value for status in Status}:
        return _error("status 包含无效值")

    priority = request.args.get("priority") or None
    if priority and priority not in {item.value for item in Priority}:
        return _error("priority 不是有效值")

    try:
        tasks = storage.query(
            priority=priority,
            tag=request.args.get("tag") or None,
            include_archived=request.args.get("include_archived", "").lower() in {"1", "true", "yes"},
            sort_by=request.args.get("sort_by", "created_at"),
            reverse=request.args.get("reverse", "").lower() in {"1", "true", "yes"},
            project_id=project_id,
            statuses=status_values,
        )
    except ValueError as exc:
        return _error(str(exc))
    page_tasks, meta = _paginate(tasks, page, page_size)
    return jsonify({"data": [_task_data(task, storage) for task in page_tasks], "meta": meta})


@api_bp.route("/tasks", methods=["POST"])
@api_bp.route("/tasks/", methods=["POST"])
def create_task_api():
    storage = JSONStorage()
    values = _parse_task_values(_payload(), storage)
    task = storage.add(Task(**values))
    return jsonify({"data": _task_data(task, storage)}), 201


@api_bp.route("/tasks/<int:task_id>", methods=["GET"])
def get_task_api(task_id: int):
    storage = JSONStorage()
    task = storage.get_by_id(task_id)
    if task is None:
        return _error("任务不存在", 404, "not_found")
    return jsonify({"data": _task_data(task, storage)})


@api_bp.route("/tasks/<int:task_id>", methods=["PATCH"])
def update_task_api(task_id: int):
    storage = JSONStorage()
    task = storage.get_by_id(task_id)
    if task is None:
        return _error("任务不存在", 404, "not_found")
    values = _parse_task_values(_payload(), storage, partial=True)
    for key, value in values.items():
        setattr(task, key, value)
    storage.update(task)
    return jsonify({"data": _task_data(task, storage)})


@api_bp.route("/tasks/<int:task_id>", methods=["DELETE"])
def archive_task_api(task_id: int):
    storage = JSONStorage()
    task = storage.get_by_id(task_id)
    if task is None:
        return _error("任务不存在", 404, "not_found")
    if not task.archived:
        storage.archive(task_id)
    return jsonify({"data": _task_data(task, storage)})


@api_bp.route("/projects", methods=["GET"])
@api_bp.route("/projects/", methods=["GET"])
def list_projects_api():
    storage = JSONStorage()
    page, page_size = _pagination_args()
    projects = storage.get_projects()
    page_projects, meta = _paginate(projects, page, page_size)
    return jsonify({"data": [_project_data(project, storage) for project in page_projects], "meta": meta})


@api_bp.route("/projects", methods=["POST"])
@api_bp.route("/projects/", methods=["POST"])
def create_project_api():
    payload = _payload()
    name = payload.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ApiInputError("name 不能为空")
    description = payload.get("description", "")
    if not isinstance(description, str):
        raise ApiInputError("description 必须是字符串")
    storage = JSONStorage()
    project = storage.add_project(Project(name=name.strip(), description=description))
    return jsonify({"data": _project_data(project, storage)}), 201


@api_bp.route("/projects/<int:project_id>", methods=["GET"])
def get_project_api(project_id: int):
    storage = JSONStorage()
    project = storage.get_project_by_id(project_id)
    if project is None:
        return _error("项目不存在", 404, "not_found")
    include_archived = request.args.get("include_archived", "").lower() in {"1", "true", "yes"}
    tasks = storage.get_all(include_archived=include_archived, project_id=project_id)
    page, page_size = _pagination_args()
    page_tasks, meta = _paginate(tasks, page, page_size)
    return jsonify(
        {
            "data": {
                **_project_data(project, storage),
                "tasks": [_task_data(task, storage) for task in page_tasks],
            },
            "meta": meta,
        }
    )
