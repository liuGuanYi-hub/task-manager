"""项目管理路由"""
from flask import Blueprint, render_template_string, request, redirect, url_for
from storage.json_storage import JSONStorage
from models.task import Task, Status
from collections import Counter

projects_bp = Blueprint('projects', __name__, url_prefix='/projects')

# 项目列表页面模板
PROJECTS_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>项目管理 - 任务管理系统</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .nav {
            display: flex;
            background: #f8f9fa;
            padding: 15px 30px;
            gap: 20px;
            border-bottom: 2px solid #e9ecef;
            flex-wrap: wrap;
        }
        .nav a {
            text-decoration: none;
            color: #495057;
            padding: 10px 20px;
            border-radius: 5px;
            transition: all 0.3s;
        }
        .nav a:hover, .nav a.active {
            background: #667eea;
            color: white;
        }
        .content { padding: 30px; }
        .projects-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .project-card {
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            overflow: hidden;
            transition: all 0.3s;
            cursor: pointer;
        }
        .project-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .project-header {
            padding: 20px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }
        .project-body {
            padding: 20px;
        }
        .project-title {
            font-size: 1.3em;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .project-description {
            color: #6c757d;
            margin-bottom: 15px;
            line-height: 1.6;
        }
        .project-stats {
            display: flex;
            justify-content: space-between;
            padding-top: 15px;
            border-top: 1px solid #e9ecef;
        }
        .stat-item {
            text-align: center;
        }
        .stat-number {
            font-size: 1.5em;
            font-weight: bold;
            color: #667eea;
        }
        .stat-label {
            font-size: 0.8em;
            color: #6c757d;
            margin-top: 5px;
        }
        .progress-bar {
            height: 8px;
            background: #e9ecef;
            border-radius: 4px;
            overflow: hidden;
            margin: 15px 0;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #28a745, #20c997);
            transition: width 0.5s ease;
        }
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #6c757d;
        }
        .empty-state h3 {
            font-size: 1.5em;
            margin-bottom: 10px;
        }
        .btn {
            padding: 12px 24px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
            text-decoration: none;
            display: inline-block;
            margin-top: 20px;
        }
        .btn:hover {
            background: #5568d3;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📁 项目管理</h1>
            <p>组织和管理您的任务项目</p>
        </div>
        <div class="nav">
            <a href="/">📋 任务列表</a>
            <a href="/stats">📊 统计仪表板</a>
            <a href="/calendar">📅 日历视图</a>
            <a href="/projects" class="active">📁 项目管理</a>
            <a href="/settings">⚙️ 设置</a>
        </div>
        <div class="content">
            {% if projects %}
            <div class="projects-grid">
                {% for project in projects %}
                <div class="project-card" onclick="location.href='/projects/{{ project.id }}'">
                    <div class="project-header">
                        <div class="project-title">{{ project.name }}</div>
                    </div>
                    <div class="project-body">
                        {% if project.description %}
                        <div class="project-description">{{ project.description }}</div>
                        {% endif %}
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {{ project.completion_rate }}%"></div>
                        </div>
                        <div class="project-stats">
                            <div class="stat-item">
                                <div class="stat-number">{{ project.total_tasks }}</div>
                                <div class="stat-label">总任务</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-number">{{ project.completed_tasks }}</div>
                                <div class="stat-label">已完成</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-number">{{ project.completion_rate }}%</div>
                                <div class="stat-label">完成率</div>
                            </div>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
            {% else %}
            <div class="empty-state">
                <h3>暂无项目</h3>
                <p>创建第一个项目来组织您的任务</p>
                <a href="/projects/new" class="btn">创建项目</a>
            </div>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""


@projects_bp.route('/')
def projects_list():
    """项目列表"""
    storage = JSONStorage()
    tasks = storage.get_all()
    
    # 按标签分组作为项目
    projects_dict = {}
    for task in tasks:
        for tag in task.tags:
            if tag not in projects_dict:
                projects_dict[tag] = {
                    'id': tag,
                    'name': tag,
                    'description': f'包含标签 "{tag}" 的所有任务',
                    'tasks': []
                }
            projects_dict[tag]['tasks'].append(task)
    
    # 计算项目统计
    projects = []
    for tag, data in projects_dict.items():
        total = len(data['tasks'])
        completed = sum(1 for t in data['tasks'] if t.status == Status.DONE)
        completion_rate = round((completed / total * 100), 1) if total > 0 else 0
        
        projects.append({
            'id': tag,
            'name': data['name'],
            'description': data['description'],
            'total_tasks': total,
            'completed_tasks': completed,
            'completion_rate': completion_rate
        })
    
    # 按任务数排序
    projects.sort(key=lambda x: x['total_tasks'], reverse=True)
    
    return render_template_string(
        PROJECTS_TEMPLATE,
        projects=projects
    )


@projects_bp.route('/<project_id>')
def project_detail(project_id):
    """项目详情"""
    storage = JSONStorage()
    tasks = storage.get_all()
    
    # 筛选项目任务
    project_tasks = [t for t in tasks if project_id in t.tags]
    
    if not project_tasks:
        return redirect(url_for('projects.projects_list'))
    
    # 项目统计
    total = len(project_tasks)
    completed = sum(1 for t in project_tasks if t.status == Status.DONE)
    completion_rate = round((completed / total * 100), 1) if total > 0 else 0
    
    return render_template_string(
        PROJECT_DETAIL_TEMPLATE,
        project_name=project_id,
        tasks=project_tasks,
        total=total,
        completed=completed,
        completion_rate=completion_rate
    )


# 项目详情页面模板
PROJECT_DETAIL_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ project_name }} - 项目管理</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .nav {
            display: flex;
            background: #f8f9fa;
            padding: 15px 30px;
            gap: 20px;
            border-bottom: 2px solid #e9ecef;
        }
        .nav a {
            text-decoration: none;
            color: #495057;
            padding: 10px 20px;
            border-radius: 5px;
            transition: all 0.3s;
        }
        .nav a:hover, .nav a.active {
            background: #667eea;
            color: white;
        }
        .stats-bar {
            display: flex;
            gap: 30px;
            padding: 20px 30px;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
        }
        .stat-item {
            text-align: center;
        }
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        .stat-label {
            color: #6c757d;
            margin-top: 5px;
        }
        .content { padding: 30px; }
        .task-list {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        .task-item {
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            border-left: 4px solid #667eea;
            display: flex;
            align-items: center;
            gap: 15px;
        }
        .task-item.done {
            border-left-color: #28a745;
            opacity: 0.7;
        }
        .task-title {
            flex: 1;
            font-size: 1.1em;
            font-weight: 500;
        }
        .task-meta {
            display: flex;
            gap: 15px;
            color: #6c757d;
            font-size: 0.9em;
        }
        .back-btn {
            display: inline-block;
            margin: 20px 30px;
            padding: 10px 20px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📁 项目：{{ project_name }}</h1>
        </div>
        <div class="nav">
            <a href="/">📋 任务列表</a>
            <a href="/stats">📊 统计仪表板</a>
            <a href="/calendar">📅 日历视图</a>
            <a href="/projects" class="active">📁 项目管理</a>
            <a href="/settings">⚙️ 设置</a>
        </div>
        <div class="stats-bar">
            <div class="stat-item">
                <div class="stat-number">{{ total }}</div>
                <div class="stat-label">总任务</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{{ completed }}</div>
                <div class="stat-label">已完成</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{{ completion_rate }}%</div>
                <div class="stat-label">完成率</div>
            </div>
        </div>
        <div class="content">
            <div class="task-list">
                {% for task in tasks %}
                <div class="task-item {{ 'done' if task.status.value == '已完成' else '' }}">
                    <div style="font-size: 1.5em;">
                        {% if task.status.value == '已完成' %}✅
                        {% elif task.status.value == '进行中' %}🔄
                        {% else %}⬜{% endif %}
                    </div>
                    <div style="font-size: 1.5em;">
                        {% if task.priority.value == '高' %}🔴
                        {% elif task.priority.value == '中' %}🟡
                        {% else %}🟢{% endif %}
                    </div>
                    <div class="task-title">{{ task.title }}</div>
                    <div class="task-meta">
                        <span>{{ task.status.value }}</span>
                        <span>{{ task.priority.value }}</span>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        <a href="/projects" class="back-btn">← 返回项目列表</a>
    </div>
</body>
</html>
"""
