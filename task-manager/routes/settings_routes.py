"""设置页面路由"""
from flask import Blueprint, render_template_string, request, redirect, url_for, flash, send_file
from storage.json_storage import JSONStorage
import json
import io
from datetime import datetime

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

# 设置页面模板
SETTINGS_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>设置 - 任务管理系统</title>
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
        .settings-section {
            margin-bottom: 30px;
            background: #f8f9fa;
            border-radius: 10px;
            padding: 25px;
        }
        .settings-section h2 {
            color: #495057;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e9ecef;
        }
        .setting-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px 0;
            border-bottom: 1px solid #e9ecef;
        }
        .setting-item:last-child {
            border-bottom: none;
        }
        .setting-label {
            font-weight: 500;
            color: #495057;
        }
        .setting-control {
            display: flex;
            gap: 10px;
        }
        .btn {
            padding: 10px 20px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.9em;
            text-decoration: none;
            display: inline-block;
        }
        .btn:hover {
            background: #5568d3;
        }
        .btn-success {
            background: #28a745;
        }
        .btn-danger {
            background: #dc3545;
        }
        .btn-warning {
            background: #ffc107;
            color: #333;
        }
        .theme-preview {
            display: flex;
            gap: 10px;
            margin-top: 10px;
        }
        .theme-option {
            width: 60px;
            height: 60px;
            border-radius: 10px;
            cursor: pointer;
            border: 3px solid transparent;
            transition: all 0.3s;
        }
        .theme-option:hover, .theme-option.active {
            border-color: #667eea;
            transform: scale(1.1);
        }
        .stats-info {
            padding: 15px;
            background: white;
            border-radius: 8px;
            margin-top: 15px;
        }
        .stat-row {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #f8f9fa;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚙️ 设置</h1>
            <p>自定义您的任务管理系统</p>
        </div>
        <div class="nav">
            <a href="/">📋 任务列表</a>
            <a href="/stats">📊 统计仪表板</a>
            <a href="/calendar">📅 日历视图</a>
            <a href="/projects">📁 项目管理</a>
            <a href="/settings" class="active">⚙️ 设置</a>
        </div>
        <div class="content">
            <!-- 外观设置 -->
            <div class="settings-section">
                <h2>🎨 外观设置</h2>
                <div class="setting-item">
                    <div class="setting-label">主题颜色</div>
                    <div class="setting-control">
                        <div class="theme-preview">
                            <div class="theme-option active" style="background: linear-gradient(135deg, #667eea, #764ba2);"></div>
                            <div class="theme-option" style="background: linear-gradient(135deg, #f093fb, #f5576c);"></div>
                            <div class="theme-option" style="background: linear-gradient(135deg, #4facfe, #00f2fe);"></div>
                            <div class="theme-option" style="background: linear-gradient(135deg, #43e97b, #38f9d7);"></div>
                        </div>
                    </div>
                </div>
                <div class="setting-item">
                    <div class="setting-label">深色模式</div>
                    <div class="setting-control">
                        <button class="btn" disabled>即将推出</button>
                    </div>
                </div>
            </div>

            <!-- 数据管理 -->
            <div class="settings-section">
                <h2>💾 数据管理</h2>
                <div class="setting-item">
                    <div class="setting-label">导出数据</div>
                    <div class="setting-control">
                        <a href="/settings/export/json" class="btn">导出为 JSON</a>
                        <a href="/settings/export/csv" class="btn btn-success">导出为 CSV</a>
                    </div>
                </div>
                <div class="setting-item">
                    <div class="setting-label">导入数据</div>
                    <div class="setting-control">
                        <button class="btn btn-warning" disabled>即将推出</button>
                    </div>
                </div>
                <div class="stats-info">
                    <div class="stat-row">
                        <span>总任务数:</span>
                        <strong>{{ total_tasks }}</strong>
                    </div>
                    <div class="stat-row">
                        <span>数据文件大小:</span>
                        <strong>{{ file_size }}</strong>
                    </div>
                    <div class="stat-row">
                        <span>最后更新:</span>
                        <strong>{{ last_modified }}</strong>
                    </div>
                </div>
            </div>

            <!-- 通知设置 -->
            <div class="settings-section">
                <h2>🔔 通知设置</h2>
                <div class="setting-item">
                    <div class="setting-label">任务到期提醒</div>
                    <div class="setting-control">
                        <button class="btn" disabled>即将推出</button>
                    </div>
                </div>
                <div class="setting-item">
                    <div class="setting-label">每日摘要</div>
                    <div class="setting-control">
                        <button class="btn" disabled>即将推出</button>
                    </div>
                </div>
            </div>

            <!-- 系统信息 -->
            <div class="settings-section">
                <h2>ℹ️ 系统信息</h2>
                <div class="setting-item">
                    <div class="setting-label">版本</div>
                    <div class="setting-control">
                        <span style="color: #6c757d;">v1.0.0</span>
                    </div>
                </div>
                <div class="setting-item">
                    <div class="setting-label">技术栈</div>
                    <div class="setting-control">
                        <span style="color: #6c757d;">Python + Flask + Chart.js</span>
                    </div>
                </div>
                <div class="setting-item">
                    <div class="setting-label">GitHub 仓库</div>
                    <div class="setting-control">
                        <a href="https://github.com/liuGuanYi-hub/task-manager" target="_blank" class="btn">查看</a>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""


@settings_bp.route('/')
def settings_page():
    """设置页面"""
    storage = JSONStorage()
    tasks = storage.get_all()
    
    # 获取文件信息
    import os
    from pathlib import Path
    
    db_path = Path(storage.db_path)
    if db_path.exists():
        file_size = f"{db_path.stat().st_size / 1024:.2f} KB"
        last_modified = datetime.fromtimestamp(db_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
    else:
        file_size = "0 KB"
        last_modified = "无数据"
    
    return render_template_string(
        SETTINGS_TEMPLATE,
        total_tasks=len(tasks),
        file_size=file_size,
        last_modified=last_modified
    )


@settings_bp.route('/export/<format>')
def export_data(format):
    """导出数据"""
    storage = JSONStorage()
    tasks = storage.get_all()
    
    if format == 'json':
        # 导出为 JSON
        data = {
            'export_date': datetime.now().isoformat(),
            'total_tasks': len(tasks),
            'tasks': [task.to_dict() for task in tasks]
        }
        
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        return send_file(
            io.BytesIO(json_str.encode('utf-8')),
            mimetype='application/json',
            as_attachment=True,
            download_name=f'tasks_export_{datetime.now().strftime("%Y%m%d")}.json'
        )
    
    elif format == 'csv':
        # 导出为 CSV
        import csv
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入表头
        writer.writerow(['ID', '标题', '描述', '优先级', '状态', '创建时间', '截止时间', '标签'])
        
        # 写入数据
        for task in tasks:
            writer.writerow([
                task.id,
                task.title,
                task.description,
                task.priority.value,
                task.status.value,
                task.created_at.strftime('%Y-%m-%d'),
                task.due_date.strftime('%Y-%m-%d') if task.due_date else '',
                ', '.join(task.tags)
            ])
        
        csv_data = output.getvalue()
        return send_file(
            io.BytesIO(csv_data.encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'tasks_export_{datetime.now().strftime("%Y%m%d")}.csv'
        )
    
    return redirect(url_for('settings.settings_page'))
