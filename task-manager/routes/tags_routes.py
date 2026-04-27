"""标签管理路由"""
from flask import Blueprint, render_template_string, request, redirect, url_for
from storage.json_storage import JSONStorage
from collections import Counter

tags_bp = Blueprint('tags', __name__, url_prefix='/stats/tags')

TAGS_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>标签管理 - 任务管理系统</title>
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
        .tags-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .tag-card {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.3s;
        }
        .tag-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        }
        .tag-info {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        .tag-color {
            width: 20px;
            height: 20px;
            border-radius: 5px;
        }
        .tag-name {
            font-size: 1.2em;
            font-weight: bold;
            color: #495057;
        }
        .tag-count {
            background: #667eea;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
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
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏷️ 标签管理</h1>
            <p>管理和查看所有标签</p>
        </div>
        <div class="nav">
            <a href="/stats" class="active">📈 统计仪表板</a>
            <a href="/stats/weekly">📅 周报</a>
            <a href="/stats/tags" class="active">🏷️ 标签</a>
            <a href="/">← 返回任务</a>
        </div>
        <div class="content">
            {% if tags %}
            <div class="tags-grid">
                {% for tag, count in tags %}
                <div class="tag-card">
                    <div class="tag-info">
                        <div class="tag-color" style="background: {{ colors[loop.index0 % colors|length] }}"></div>
                        <div>
                            <div class="tag-name">#{{ tag }}</div>
                        </div>
                    </div>
                    <div class="tag-count">{{ count }} 个任务</div>
                </div>
                {% endfor %}
            </div>
            {% else %}
            <div class="empty-state">
                <h3>暂无标签</h3>
                <p>创建任务时添加标签，标签会显示在这里</p>
            </div>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""


@tags_bp.route('/')
def tags_page():
    """标签管理页面"""
    storage = JSONStorage()
    tasks = storage.get_all()
    
    # 统计标签
    all_tags = []
    for task in tasks:
        all_tags.extend(task.tags)
    
    tag_count = Counter(all_tags)
    tags = tag_count.most_common(20)  # 显示前 20 个标签
    
    # 标签颜色
    colors = [
        '#667eea', '#764ba2', '#f093fb', '#f5576c',
        '#4facfe', '#00f2fe', '#43e97b', '#38f9d7',
        '#fa709a', '#fee140', '#30cfd0', '#330867'
    ]
    
    return render_template_string(
        TAGS_TEMPLATE,
        tags=tags,
        colors=colors
    )
