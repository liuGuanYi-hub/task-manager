"""全局任务、项目和标签搜索路由。"""

from flask import Blueprint, jsonify, request, url_for

from storage.factory import create_storage as JSONStorage


search_bp = Blueprint("search", __name__, url_prefix="/search")
_MAX_RESULTS = 30


def _matches(query: str, *values) -> bool:
    if not query:
        return True
    haystack = " ".join(str(value or "") for value in values).casefold()
    return query.casefold() in haystack


def _task_result(task, project_name: str) -> dict:
    return {
        "kind": "task",
        "icon": "↗",
        "accent": "blue",
        "title": task.title,
        "subtitle": f"任务 · {task.status.value} · {project_name}",
        "url": url_for("edit_task", task_id=task.id),
    }


@search_bp.route("")
@search_bp.route("/")
def search_api():
    """返回当前存储中的匹配结果；空查询返回最近任务和全部项目/标签的前 30 项。"""
    query = request.args.get("q", "").strip()
    storage = JSONStorage()
    projects = storage.get_projects()
    project_names = {project.id: project.name for project in projects}
    results = []

    tasks = storage.query(sort_by="updated_at", reverse=True)
    for task in tasks:
        project_name = project_names.get(task.project_id, "未归属项目")
        if _matches(query, task.title, task.description, project_name, *task.tags):
            results.append(_task_result(task, project_name))
        if len(results) >= _MAX_RESULTS:
            break

    if len(results) < _MAX_RESULTS:
        for project in projects:
            if _matches(query, project.name, project.description):
                results.append(
                    {
                        "kind": "project",
                        "icon": "▤",
                        "accent": "violet",
                        "title": project.name,
                        "subtitle": "项目 · 项目详情",
                        "url": url_for("projects.project_detail", project_id=project.id),
                    }
                )
            if len(results) >= _MAX_RESULTS:
                break

    if len(results) < _MAX_RESULTS:
        seen_tags = set()
        for task in tasks:
            for tag in task.tags:
                if tag in seen_tags:
                    continue
                seen_tags.add(tag)
                if _matches(query, tag):
                    results.append(
                        {
                            "kind": "tag",
                            "icon": "#",
                            "accent": "green",
                            "title": tag,
                            "subtitle": "标签 · 相关任务筛选",
                            "url": url_for("views.views_page", tag=tag),
                        }
                    )
                if len(results) >= _MAX_RESULTS:
                    break
            if len(results) >= _MAX_RESULTS:
                break

    return jsonify({"data": results[:_MAX_RESULTS], "meta": {"query": query, "count": len(results[:_MAX_RESULTS])}})
