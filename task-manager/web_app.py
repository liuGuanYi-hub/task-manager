"""简单的 Web 界面"""
from flask import Flask, render_template_string, request, jsonify, redirect, url_for
from storage.json_storage import JSONStorage
from models.task import Task, Priority, Status
from datetime import datetime
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

# HTML 模板
BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>任务管理系统</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .stats {
            display: flex;
            justify-content: space-around;
            padding: 20px;
            background: #f8f9fa;
        }
        .stat-item { text-align: center; }
        .stat-number { font-size: 2em; font-weight: bold; color: #667eea; }
        .stat-label { color: #666; margin-top: 5px; }
        .content { padding: 30px; }
        .form-group { margin-bottom: 20px; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
        .form-group input, .form-group select, .form-group textarea {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s;
        }
        .btn-primary { background: #667eea; color: white; }
        .btn-primary:hover { background: #5568d3; }
        .btn-success { background: #28a745; color: white; }
        .btn-danger { background: #dc3545; color: white; }
        .btn-warning { background: #ffc107; color: #333; }
        .task-list { margin-top: 30px; }
        .task-item {
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 5px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .task-item.done { border-left-color: #28a745; opacity: 0.7; }
        .task-item.in-progress { border-left-color: #ffc107; }
        .task-info { flex: 1; }
        .task-title { font-size: 1.2em; font-weight: bold; margin-bottom: 5px; }
        .task-meta { color: #666; font-size: 0.9em; }
        .task-actions { display: flex; gap: 10px; }
        .priority-high { color: #dc3545; }
        .priority-medium { color: #ffc107; }
        .priority-low { color: #28a745; }
        .tabs { display: flex; border-bottom: 2px solid #ddd; margin-bottom: 20px; }
        .tab {
            padding: 10px 20px;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            margin-bottom: -2px;
        }
        .tab.active { border-bottom-color: #667eea; color: #667eea; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📋 任务管理系统</h1>
            <p>高效管理你的日常任务</p>
        </div>
        <div style="background: #f8f9fa; padding: 15px 30px; display: flex; gap: 15px; flex-wrap: wrap;">
            <a href="/" style="text-decoration: none; color: #495057; padding: 8px 16px; background: white; border-radius: 5px;">📋 任务列表</a>
            <a href="/new" style="text-decoration: none; color: #495057; padding: 8px 16px; background: white; border-radius: 5px;">➕ 新建任务</a>
            <a href="/stats" style="text-decoration: none; color: #495057; padding: 8px 16px; background: white; border-radius: 5px;">📊 统计仪表板</a>
            <a href="/calendar" style="text-decoration: none; color: #495057; padding: 8px 16px; background: white; border-radius: 5px;">📅 日历视图</a>
            <a href="/projects" style="text-decoration: none; color: #495057; padding: 8px 16px; background: white; border-radius: 5px;">📁 项目管理</a>
            <a href="/settings" style="text-decoration: none; color: #495057; padding: 8px 16px; background: white; border-radius: 5px;">⚙️ 设置</a>
        </div>
        {% block content %}{% endblock %}
    </div>
</body>
</html>
"""

INDEX_PAGE = BASE_TEMPLATE.replace(
    "{% block content %}{% endblock %}",
    """
        <div class="stats">
            <div class="stat-item">
                <div class="stat-number">{{ total }}</div>
                <div class="stat-label">总任务</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{{ todo }}</div>
                <div class="stat-label">待办</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{{ in_progress }}</div>
                <div class="stat-label">进行中</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{{ done }}</div>
                <div class="stat-label">已完成</div>
            </div>
        </div>
        <div class="content">
            <div class="tabs">
                <div class="tab active" onclick="location.href='/'">全部任务</div>
                <div class="tab" onclick="location.href='/new'">新建任务</div>
            </div>
            <div class="task-list">
                {% for task in tasks %}
                <div class="task-item {{ task.status_class }}">
                    <div class="task-info">
                        <div class="task-title">
                            {% if task.status.value == '已完成' %}✅{% elif task.status.value == '进行中' %}🔄{% else %}⬜{% endif %}
                            {{ task.title }}
                            <span class="priority-{{ task.priority_class }}">
                                {% if task.priority.value == '高' %}🔴{% elif task.priority.value == '中' %}🟡{% else %}🟢{% endif %}
                            </span>
                        </div>
                        <div class="task-meta">
                            {% if task.description %}{{ task.description }}{% endif %}
                            {% if task.tags %} | 标签：{{ task.tags|join(', ') }}{% endif %}
                        </div>
                    </div>
                    <div class="task-actions">
                        <form method="POST" action="/task/{{ task.id }}/toggle" style="display:inline;">
                            <button type="submit" class="btn btn-{{ 'success' if task.status.value != '已完成' else 'warning' }}">
                                {{ '完成' if task.status.value != '已完成' else '撤销' }}
                            </button>
                        </form>
                        <a href="/task/{{ task.id }}/edit" class="btn btn-warning">编辑</a>
                        <form method="POST" action="/task/{{ task.id }}/delete" style="display:inline;" onsubmit="return confirm('确定删除？')">
                            <button type="submit" class="btn btn-danger">删除</button>
                        </form>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    """
)

NEW_TASK_PAGE = BASE_TEMPLATE.replace(
    "{% block content %}{% endblock %}",
    """
        <div class="content">
            <div class="tabs">
                <div class="tab" onclick="location.href='/'">全部任务</div>
                <div class="tab active">新建任务</div>
            </div>
            <form method="POST" action="/new">
                <div class="form-group">
                    <label>标题 *</label>
                    <input type="text" name="title" required>
                </div>
                <div class="form-group">
                    <label>描述</label>
                    <textarea name="description" rows="3"></textarea>
                </div>
                <div class="form-group">
                    <label>优先级</label>
                    <select name="priority">
                        <option value="低">🟢 低</option>
                        <option value="中" selected>🟡 中</option>
                        <option value="高">🔴 高</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>标签（用逗号分隔）</label>
                    <input type="text" name="tags" placeholder="例如：学习，工作，重要">
                </div>
                <button type="submit" class="btn btn-primary">创建任务</button>
                <a href="/" class="btn btn-warning">取消</a>
            </form>
        </div>
    """
)

EDIT_TASK_PAGE = BASE_TEMPLATE.replace(
    "{% block content %}{% endblock %}",
    """
        <div class="content">
            <div class="tabs">
                <div class="tab" onclick="location.href='/'">全部任务</div>
                <div class="tab active">编辑任务</div>
            </div>
            <form method="POST" action="/task/{{ task.id }}/update">
                <div class="form-group">
                    <label>标题 *</label>
                    <input type="text" name="title" value="{{ task.title }}" required>
                </div>
                <div class="form-group">
                    <label>描述</label>
                    <textarea name="description" rows="3">{{ task.description }}</textarea>
                </div>
                <div class="form-group">
                    <label>优先级</label>
                    <select name="priority">
                        <option value="低" {{ 'selected' if task.priority.value == '低' else '' }}>🟢 低</option>
                        <option value="中" {{ 'selected' if task.priority.value == '中' else '' }}>🟡 中</option>
                        <option value="高" {{ 'selected' if task.priority.value == '高' else '' }}>🔴 高</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>状态</label>
                    <select name="status">
                        <option value="待办" {{ 'selected' if task.status.value == '待办' else '' }}>⬜ 待办</option>
                        <option value="进行中" {{ 'selected' if task.status.value == '进行中' else '' }}>🔄 进行中</option>
                        <option value="已完成" {{ 'selected' if task.status.value == '已完成' else '' }}>✅ 已完成</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>标签（用逗号分隔）</label>
                    <input type="text" name="tags" value="{{ task.tags|join(', ') }}">
                </div>
                <button type="submit" class="btn btn-primary">保存修改</button>
                <a href="/" class="btn btn-warning">取消</a>
            </form>
        </div>
    """
)


@app.route("/")
def index():
    """首页 - 显示所有任务"""
    tasks = storage.get_all()
    
    # 准备任务数据
    task_data = []
    for task in tasks:
        task.status_class = "done" if task.status.value == "已完成" else ("in-progress" if task.status.value == "进行中" else "")
        task.priority_class = "high" if task.priority.value == "高" else ("medium" if task.priority.value == "中" else "low")
        task_data.append(task)
    
    # 统计
    total = len(tasks)
    todo = sum(1 for t in tasks if t.status == Status.TODO)
    in_progress = sum(1 for t in tasks if t.status == Status.IN_PROGRESS)
    done = sum(1 for t in tasks if t.status == Status.DONE)
    
    return render_template_string(
        INDEX_PAGE,
        tasks=task_data,
        total=total,
        todo=todo,
        in_progress=in_progress,
        done=done
    )


@app.route("/new", methods=["GET", "POST"])
def new_task():
    """新建任务"""
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description", "")
        priority = Priority(request.form.get("priority", "中"))
        tags_str = request.form.get("tags", "")
        tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []
        
        task = Task(
            title=title,
            description=description,
            priority=priority,
            tags=tags
        )
        storage.add(task)
        return redirect(url_for("index"))
    
    return render_template_string(NEW_TASK_PAGE)


@app.route("/task/<int:task_id>/edit")
def edit_task(task_id):
    """编辑任务页面"""
    task = storage.get_by_id(task_id)
    if not task:
        return "任务不存在", 404
    return render_template_string(EDIT_TASK_PAGE, task=task)


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
