"""周报路由"""
from flask import Blueprint, render_template_string
from storage.json_storage import JSONStorage
from models.task import Status
from datetime import datetime, timedelta
from collections import Counter

weekly_bp = Blueprint('weekly', __name__, url_prefix='/stats/weekly')

WEEKLY_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>周报 - 任务管理系统</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
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
        .week-selector {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
        }
        .week-nav {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        .week-nav a {
            padding: 10px 20px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 5px;
        }
        .week-nav a:hover {
            background: #5568d3;
        }
        .week-title {
            font-size: 1.5em;
            font-weight: bold;
            color: #495057;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            text-align: center;
        }
        .stat-card .number {
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }
        .stat-card .label {
            color: #6c757d;
            margin-top: 10px;
        }
        .section {
            margin-bottom: 30px;
            background: #f8f9fa;
            border-radius: 10px;
            padding: 25px;
        }
        .section h3 {
            margin-bottom: 20px;
            color: #495057;
        }
        .task-list {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .task-item {
            background: white;
            padding: 15px;
            border-radius: 5px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .task-status {
            font-size: 1.5em;
        }
        .task-title {
            flex: 1;
            font-weight: 500;
        }
        .task-date {
            color: #6c757d;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📅 周报</h1>
            <p>每周工作完成情况</p>
        </div>
        <div class="nav">
            <a href="/stats" class="active">📈 统计仪表板</a>
            <a href="/stats/weekly">📅 周报</a>
            <a href="/stats/tags">🏷️ 标签</a>
            <a href="/">← 返回任务</a>
        </div>
        <div class="content">
            <div class="week-selector">
                <div class="week-nav">
                    {% if prev_week %}
                    <a href="/stats/weekly?date={{ prev_week }}">&lt; 上周</a>
                    {% endif %}
                </div>
                <div class="week-title">
                    {{ week_start }} 至 {{ week_end }}
                </div>
                <div class="week-nav">
                    {% if next_week %}
                    <a href="/stats/weekly?date={{ next_week }}">下周 &gt;</a>
                    {% endif %}
                </div>
            </div>

            <div class="stats-grid">
                <div class="stat-card">
                    <div class="number">{{ total_created }}</div>
                    <div class="label">新建任务</div>
                </div>
                <div class="stat-card">
                    <div class="number">{{ total_completed }}</div>
                    <div class="label">完成任务</div>
                </div>
                <div class="stat-card">
                    <div class="number">{{ completion_rate }}%</div>
                    <div class="label">完成率</div>
                </div>
                <div class="stat-card">
                    <div class="number">{{ active_days }}</div>
                    <div class="label">活跃天数</div>
                </div>
            </div>

            <div class="section">
                <h3>📊 每日任务趋势</h3>
                <div style="height: 300px;">
                    <canvas id="dailyChart"></canvas>
                </div>
            </div>

            <div class="section">
                <h3>✅ 本周完成的任务</h3>
                <div class="task-list">
                    {% for task in completed_tasks %}
                    <div class="task-item">
                        <div class="task-status">✅</div>
                        <div class="task-title">{{ task.title }}</div>
                        <div class="task-date">{{ task.completed_date.strftime('%m-%d') }}</div>
                    </div>
                    {% endfor %}
                    {% if not completed_tasks %}
                    <div style="text-align: center; color: #6c757d; padding: 20px;">
                        本周暂无完成任务
                    </div>
                    {% endif %}
                </div>
            </div>

            <div class="section">
                <h3>🆕 本周新建的任务</h3>
                <div class="task-list">
                    {% for task in created_tasks %}
                    <div class="task-item">
                        <div class="task-status">🆕</div>
                        <div class="task-title">{{ task.title }}</div>
                        <div class="task-date">{{ task.created_at.strftime('%m-%d') }}</div>
                    </div>
                    {% endfor %}
                    {% if not created_tasks %}
                    <div style="text-align: center; color: #6c757d; padding: 20px;">
                        本周暂无新建任务
                    </div>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>

    <script>
        const ctx = document.getElementById('dailyChart').getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: {{ daily_labels | tojson }},
                datasets: [{
                    label: '任务数量',
                    data: {{ daily_data | tojson }},
                    backgroundColor: 'rgba(102, 126, 234, 0.6)',
                    borderColor: '#667eea',
                    borderWidth: 1,
                    borderRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
    </script>
</body>
</html>
"""


@weekly_bp.route('/')
def weekly_report():
    """周报页面"""
    from urllib.parse import parse_qs
    
    storage = JSONStorage()
    tasks = storage.get_all()
    
    # 获取当前周
    query_string = request.query_string.decode()
    params = parse_qs(query_string)
    
    if 'date' in params:
        current_date = datetime.fromisoformat(params['date'][0])
    else:
        current_date = datetime.now()
    
    # 计算周开始和结束（周一到周日）
    week_start = current_date - timedelta(days=current_date.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
    
    # 筛选本周任务
    week_tasks = [t for t in tasks if week_start <= t.created_at <= week_end]
    completed_tasks = [t for t in week_tasks if t.status == Status.DONE]
    
    # 统计数据
    total_created = len(week_tasks)
    total_completed = len(completed_tasks)
    completion_rate = round((total_completed / total_created * 100), 1) if total_created > 0 else 0
    
    # 活跃天数
    active_days = len(set(t.created_at.date() for t in week_tasks))
    
    # 每日数据
    daily_labels = []
    daily_data = []
    for i in range(7):
        day = week_start + timedelta(days=i)
        daily_labels.append(day.strftime('%m-%d'))
        count = sum(1 for t in week_tasks if t.created_at.date() == day.date())
        daily_data.append(count)
    
    # 导航
    prev_week = (week_start - timedelta(days=7)).date().isoformat()
    next_week_date = week_start + timedelta(days=7)
    next_week = next_week_date.date().isoformat() if next_week_date <= datetime.now() else None
    
    return render_template_string(
        WEEKLY_TEMPLATE,
        week_start=week_start.strftime('%Y-%m-%d'),
        week_end=week_end.strftime('%Y-%m-%d'),
        total_created=total_created,
        total_completed=total_completed,
        completion_rate=completion_rate,
        active_days=active_days,
        daily_labels=daily_labels,
        daily_data=daily_data,
        completed_tasks=completed_tasks,
        created_tasks=week_tasks,
        prev_week=prev_week,
        next_week=next_week
    )
