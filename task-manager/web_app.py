"""简单的 Web 界面"""
from flask import Flask, jsonify, render_template, request, redirect, url_for
from storage.factory import create_storage as JSONStorage
from models.task import Task, Priority, Status, parse_datetime
from routes.stats_routes import stats_bp
from routes.tags_routes import tags_bp
from routes.weekly_routes import weekly_bp
from routes.calendar_routes import calendar_bp
from routes.agenda_routes import agenda_bp
from routes.projects_routes import projects_bp
from routes.board_routes import board_bp
from routes.views_routes import views_bp
from routes.archive_routes import archive_bp
from routes.settings_routes import settings_bp
from routes.api_routes import api_bp
from routes.today_routes import today_bp
from routes.reminder_routes import reminders_bp
from routes.search_routes import search_bp
from routes.inbox_routes import inbox_bp
from routes.task_actions import task_actions_bp

app = Flask(__name__)
storage = JSONStorage()

# 注册蓝图
app.register_blueprint(stats_bp)
app.register_blueprint(tags_bp)
app.register_blueprint(weekly_bp)
app.register_blueprint(calendar_bp)
app.register_blueprint(agenda_bp)
app.register_blueprint(projects_bp)
app.register_blueprint(board_bp)
app.register_blueprint(views_bp)
app.register_blueprint(archive_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(api_bp)
app.register_blueprint(today_bp)
app.register_blueprint(reminders_bp)
app.register_blueprint(search_bp)
app.register_blueprint(inbox_bp)
app.register_blueprint(task_actions_bp)


def _is_api_request() -> bool:
    """让未知 API 路径保持 JSON 错误契约，不被网页错误页接管。"""
    return request.path.startswith("/api/")


@app.errorhandler(404)
def handle_not_found(error):
    """为网页请求提供可回到工作台的 404 页面。"""
    if _is_api_request():
        return jsonify({"error": {"code": "not_found", "message": "资源不存在"}}), 404
    return render_template(
        "error.html",
        status_code=404,
        error_title="页面没有找到",
        error_message="这个入口可能已经移动，或者地址输入有误。",
    ), 404


@app.errorhandler(500)
def handle_internal_error(error):
    """隐藏网页内部异常细节，同时保留 API 的机器可读响应。"""
    if _is_api_request():
        return jsonify({"error": {"code": "internal_error", "message": "服务器暂时无法处理请求"}}), 500
    return render_template(
        "error.html",
        status_code=500,
        error_title="页面暂时无法打开",
        error_message="服务器遇到了一点问题，请稍后重试。",
    ), 500


@app.route("/")
def index():
    """首页 - 显示所有任务"""
    tasks = storage.get_all()

    bulk_feedback = None
    bulk_action = request.args.get("bulk_action")
    try:
        bulk_count = max(0, int(request.args.get("bulk_count", "0")))
    except ValueError:
        bulk_count = 0
    if bulk_action == "complete":
        bulk_feedback = f"已批量完成 {bulk_count} 个任务。"
    elif bulk_action == "archive":
        bulk_feedback = f"已批量归档 {bulk_count} 个任务。"
    elif bulk_action in {"priority", "project", "tags"}:
        bulk_feedback = f"已批量更新 {bulk_count} 个任务。"

    task_data = []
    for task in tasks:
        task.status_class = "done" if task.status.value == "已完成" else ("in-progress" if task.status.value == "进行中" else "")
        task.priority_class = "high" if task.priority.value == "高" else ("medium" if task.priority.value == "中" else "low")
        task_data.append(task)

    total = len(tasks)
    todo = sum(1 for t in tasks if t.status == Status.TODO)
    in_progress = sum(1 for t in tasks if t.status == Status.IN_PROGRESS)
    done = sum(1 for t in tasks if t.status == Status.DONE)

    return render_template(
        "index.html",
        tasks=task_data,
        total=total,
        todo=todo,
        in_progress=in_progress,
        done=done,
        bulk_feedback=bulk_feedback,
        projects=storage.get_projects(),
    )


@app.route("/new", methods=["GET", "POST"])
def new_task():
    """新建任务"""
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description", "")
        priority = Priority(request.form.get("priority", "中"))
        due_date_raw = request.form.get("due_date", "").strip()
        try:
            due_date = parse_datetime(due_date_raw) if due_date_raw else None
        except ValueError:
            return "截止时间格式无效，请使用日期时间输入框重新提交", 400
        project_id_raw = request.form.get("project_id", "").strip()
        try:
            project_id = int(project_id_raw) if project_id_raw else None
        except ValueError:
            return "项目 ID 格式无效", 400
        if project_id is not None and storage.get_project_by_id(project_id) is None:
            return "项目不存在", 400
        tags_str = request.form.get("tags", "")
        tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []

        task = Task(
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            tags=tags,
            project_id=project_id,
        )
        storage.add(task)
        next_url = request.args.get("next")
        if next_url and next_url.startswith("/") and not next_url.startswith("//"):
            return redirect(next_url)
        return redirect(url_for("index"))

    return render_template(
        "task_form.html",
        mode="new",
        action=url_for("new_task"),
        task=None,
        projects=storage.get_projects(),
    )


@app.route("/task/<int:task_id>/edit")
def edit_task(task_id):
    """编辑任务页面"""
    task = storage.get_by_id(task_id)
    if not task:
        return "任务不存在", 404
    return render_template(
        "task_form.html",
        mode="edit",
        action=url_for("update_task", task_id=task.id),
        task=task,
        projects=storage.get_projects(),
    )


@app.route("/task/<int:task_id>/update", methods=["POST"])
def update_task(task_id):
    """更新任务"""
    task = storage.get_by_id(task_id)
    if not task:
        return "任务不存在", 404

    task.title = request.form.get("title")
    task.description = request.form.get("description", "")
    task.priority = Priority(request.form.get("priority", "中"))
    task.status = Status(request.form.get("status", "待办"))
    due_date_raw = request.form.get("due_date", "").strip()
    try:
        task.due_date = parse_datetime(due_date_raw) if due_date_raw else None
    except ValueError:
        return "截止时间格式无效，请使用日期时间输入框重新提交", 400
    if "project_id" in request.form:
        project_id_raw = request.form.get("project_id", "").strip()
        try:
            task.project_id = int(project_id_raw) if project_id_raw else None
        except ValueError:
            return "项目 ID 格式无效", 400
        if task.project_id is not None and storage.get_project_by_id(task.project_id) is None:
            return "项目不存在", 400
    tags_str = request.form.get("tags", "")
    task.tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []

    storage.update(task)
    next_url = request.args.get("next")
    if next_url and next_url.startswith("/") and not next_url.startswith("//"):
        return redirect(next_url)
    return redirect(url_for("index"))


@app.route("/task/<int:task_id>/toggle", methods=["POST"])
def toggle_task(task_id):
    """切换任务状态"""
    task = storage.get_by_id(task_id)
    if not task:
        return "任务不存在", 404

    if task.status == Status.DONE:
        task.status = Status.TODO
    else:
        task.status = Status.DONE

    storage.update(task)
    next_url = request.args.get("next")
    if next_url and next_url.startswith("/") and not next_url.startswith("//"):
        return redirect(next_url)
    return redirect(url_for("index"))


@app.route("/tasks/bulk", methods=["POST"])
def bulk_tasks():
    """批量完成、归档或修改任务属性，复用现有存储语义。"""
    wants_json = request.is_json or "application/json" in request.headers.get("Accept", "")
    payload = request.get_json(silent=True) if request.is_json else request.form
    payload = payload if payload is not None and hasattr(payload, "get") else {}
    raw_ids = payload.get("task_ids", []) if request.is_json else request.form.getlist("task_ids")
    if isinstance(raw_ids, (str, int)):
        raw_ids = [raw_ids]
    action = str(payload.get("action", "")).strip().lower()
    task_ids = []
    for raw_id in raw_ids if isinstance(raw_ids, (list, tuple)) else []:
        try:
            task_id = int(raw_id)
        except (TypeError, ValueError):
            continue
        if task_id not in task_ids:
            task_ids.append(task_id)

    if action not in {"complete", "archive", "priority", "project", "tags"}:
        error = {"code": "invalid_action", "message": "批量操作类型无效"}
        return (jsonify({"error": error}), 400) if wants_json else (error["message"], 400)
    if not task_ids:
        error = {"code": "empty_selection", "message": "请至少选择一个任务"}
        return (jsonify({"error": error}), 400) if wants_json else (error["message"], 400)

    selected_priority = None
    selected_project_id = None
    selected_tags = None
    if action == "priority":
        try:
            selected_priority = Priority(str(payload.get("priority", "")).strip())
        except ValueError:
            error = {"code": "invalid_priority", "message": "批量优先级无效"}
            return (jsonify({"error": error}), 400) if wants_json else (error["message"], 400)
    elif action == "project":
        raw_project_id = payload.get("project_id")
        if raw_project_id == "none" or (request.is_json and raw_project_id is None):
            selected_project_id = None
        else:
            try:
                selected_project_id = int(str(raw_project_id).strip())
            except (TypeError, ValueError):
                error = {"code": "invalid_project", "message": "请选择有效项目或清除项目"}
                return (jsonify({"error": error}), 400) if wants_json else (error["message"], 400)
            if storage.get_project_by_id(selected_project_id) is None:
                error = {"code": "invalid_project", "message": "项目不存在"}
                return (jsonify({"error": error}), 400) if wants_json else (error["message"], 400)
    elif action == "tags":
        raw_tags = payload.get("tags", [])
        raw_tags = raw_tags if isinstance(raw_tags, list) else str(raw_tags).split(",")
        selected_tags = []
        for raw_tag in raw_tags:
            tag = str(raw_tag).strip()
            if tag and tag not in selected_tags:
                selected_tags.append(tag)

    changed = 0
    for task_id in task_ids:
        task = storage.get_by_id(task_id)
        if task is None or task.archived:
            continue
        if action == "complete":
            if task.status != Status.DONE:
                task.status = Status.DONE
                storage.update(task)
            changed += 1
        elif action == "archive":
            if storage.archive(task_id):
                changed += 1
        elif action == "priority":
            task.priority = selected_priority
            storage.update(task)
            changed += 1
        elif action == "project":
            task.project_id = selected_project_id
            storage.update(task)
            changed += 1
        elif action == "tags":
            task.tags = selected_tags
            storage.update(task)
            changed += 1

    if wants_json:
        return jsonify({"data": {"action": action, "updated": changed}})

    next_url = payload.get("next") or request.args.get("next")
    if next_url and next_url.startswith("/") and not next_url.startswith("//"):
        if next_url == "/":
            return redirect(url_for("index", bulk_action=action, bulk_count=changed))
        return redirect(next_url)
    return redirect(url_for("index", bulk_action=action, bulk_count=changed))


@app.route("/task/<int:task_id>/delete", methods=["POST"])
def delete_task(task_id):
    """归档任务，保留数据并从日常列表隐藏。"""
    if not storage.archive(task_id):
        return "任务不存在", 404
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
