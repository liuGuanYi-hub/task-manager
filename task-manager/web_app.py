"""简单的 Web 界面"""
from flask import Flask, render_template, request, redirect, url_for
from storage.json_storage import JSONStorage
from models.task import Task, Priority, Status, parse_datetime
from routes.stats_routes import stats_bp
from routes.tags_routes import tags_bp
from routes.weekly_routes import weekly_bp
from routes.calendar_routes import calendar_bp
from routes.projects_routes import projects_bp
from routes.settings_routes import settings_bp

app = Flask(__name__)
storage = JSONStorage()

# 注册蓝图
app.register_blueprint(stats_bp)
app.register_blueprint(tags_bp)
app.register_blueprint(weekly_bp)
app.register_blueprint(calendar_bp)
app.register_blueprint(projects_bp)
app.register_blueprint(settings_bp)


@app.route("/")
def index():
    """首页 - 显示所有任务"""
    tasks = storage.get_all()

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
    return redirect(url_for("index"))


@app.route("/task/<int:task_id>/delete", methods=["POST"])
def delete_task(task_id):
    """删除任务"""
    storage.delete(task_id)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
