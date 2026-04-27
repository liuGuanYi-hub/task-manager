"""统计路由"""
from flask import Blueprint, render_template_string, request, jsonify
from storage.json_storage import JSONStorage
from models.task import Status, Priority
from datetime import datetime, timedelta
from collections import Counter, defaultdict

stats_bp = Blueprint('stats', __name__, url_prefix='/stats')

# 统计仪表板页面模板
STATS_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>统计仪表板 - 任务管理系统</title>
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
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            border-left: 4px solid #667eea;
        }
        .stat-card h3 {
            color: #6c757d;
            font-size: 0.9em;
            margin-bottom: 10px;
            text-transform: uppercase;
        }
        .stat-card .number {
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }
        .stat-card .change {
            margin-top: 10px;
            font-size: 0.9em;
        }
        .stat-card .change.positive { color: #28a745; }
        .stat-card .change.negative { color: #dc3545; }
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .chart-card {
            background: white;
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .chart-card h3 {
            margin-bottom: 20px;
            color: #495057;
        }
        .chart-container {
            position: relative;
            height: 300px;
        }
        .progress-section {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 30px;
        }
        .progress-bar {
            background: #e9ecef;
            border-radius: 10px;
            height: 30px;
            overflow: hidden;
            margin: 15px 0;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            transition: width 0.5s ease;
        }
        .tag-cloud {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 15px;
        }
        .tag-item {
            padding: 8px 16px;
            background: #667eea;
            color: white;
            border-radius: 20px;
            font-size: 0.9em;
        }
        .tag-item span {
            background: rgba(255,255,255,0.3);
            padding: 2px 8px;
            border-radius: 10px;
            margin-left: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 统计仪表板</h1>
            <p>数据驱动，高效管理</p>
        </div>
        <div class="nav">
            <a href="/" class="active">📈 总览</a>
            <a href="/stats/weekly">📅 周报</a>
            <a href="/stats/tags">🏷️ 标签</a>
            <a href="/">← 返回任务</a>
        </div>
        <div class="content">
            <div class="stats-grid">
                <div class="stat-card">
                    <h3>总任务数</h3>
                    <div class="number">{{ total }}</div>
                    <div class="change positive">📈 全部任务</div>
                </div>
                <div class="stat-card">
                    <h3>待办任务</h3>
                    <div class="number">{{ todo }}</div>
                    <div class="change">⬜ 待处理</div>
                </div>
                <div class="stat-card">
                    <h3>进行中</h3>
                    <div class="number">{{ in_progress }}</div>
                    <div class="change">🔄 正在进行</div>
                </div>
                <div class="stat-card">
                    <h3>已完成</h3>
                    <div class="number">{{ done }}</div>
                    <div class="change positive">✅ 完成率 {{ completion_rate }}%</div>
                </div>
            </div>

            <div class="progress-section">
                <h3>🎯 总体进度</h3>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {{ completion_rate }}%">
                        {{ completion_rate }}%
                    </div>
                </div>
                <p>已完成 {{ done }} / 总共 {{ total }} 个任务</p>
            </div>

            <div class="charts-grid">
                <div class="chart-card">
                    <h3>📊 任务状态分布</h3>
                    <div class="chart-container">
                        <canvas id="statusChart"></canvas>
                    </div>
                </div>
                <div class="chart-card">
                    <h3>🎨 优先级分布</h3>
                    <div class="chart-container">
                        <canvas id="priorityChart"></canvas>
                    </div>
                </div>
            </div>

            <div class="charts-grid">
                <div class="chart-card">
                    <h3>📈 任务创建趋势</h3>
                    <div class="chart-container">
                        <canvas id="trendChart"></canvas>
                    </div>
                </div>
                <div class="chart-card">
                    <h3>🏷️ 热门标签</h3>
                    <div class="tag-cloud">
                        {% for tag, count in top_tags %}
                        <div class="tag-item">
                            {{ tag }} <span>{{ count }}</span>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // 状态分布图
        const statusCtx = document.getElementById('statusChart').getContext('2d');
        new Chart(statusCtx, {
            type: 'doughnut',
            data: {
                labels: ['待办', '进行中', '已完成'],
                datasets: [{
                    data: [{{ todo }}, {{ in_progress }}, {{ done }}],
                    backgroundColor: [
                        '#6c757d',
                        '#ffc107',
                        '#28a745'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });

        // 优先级分布图
        const priorityCtx = document.getElementById('priorityChart').getContext('2d');
        new Chart(priorityCtx, {
            type: 'pie',
            data: {
                labels: ['高优先级', '中优先级', '低优先级'],
                datasets: [{
                    data: [{{ high_count }}, {{ medium_count }}, {{ low_count }}],
                    backgroundColor: [
                        '#dc3545',
                        '#ffc107',
                        '#28a745'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });

        // 趋势图
        const trendCtx = document.getElementById('trendChart').getContext('2d');
        new Chart(trendCtx, {
            type: 'line',
            data: {
                labels: {{ trend_labels | tojson }},
                datasets: [{
                    label: '任务数量',
                    data: {{ trend_data | tojson }},
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4,
                    fill: true
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


@stats_bp.route('/')
def stats_dashboard():
    """统计仪表板"""
    storage = JSONStorage()
    tasks = storage.get_all()
    
    # 基础统计
    total = len(tasks)
    todo = sum(1 for t in tasks if t.status == Status.TODO)
    in_progress = sum(1 for t in tasks if t.status == Status.IN_PROGRESS)
    done = sum(1 for t in tasks if t.status == Status.DONE)
    completion_rate = round((done / total * 100), 1) if total > 0 else 0
    
    # 优先级统计
    high_count = sum(1 for t in tasks if t.priority == Priority.HIGH)
    medium_count = sum(1 for t in tasks if t.priority == Priority.MEDIUM)
    low_count = sum(1 for t in tasks if t.priority == Priority.LOW)
    
    # 标签统计
    all_tags = []
    for task in tasks:
        all_tags.extend(task.tags)
    tag_count = Counter(all_tags)
    top_tags = tag_count.most_common(10)
    
    # 趋势数据（最近 7 天）
    today = datetime.now()
    trend_data = []
    trend_labels = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        trend_labels.append(date_str[5:])  # 只显示月 - 日
        
        count = sum(1 for t in tasks 
                   if t.created_at.date() == date.date())
        trend_data.append(count)
    
    return render_template_string(
        STATS_TEMPLATE,
        total=total,
        todo=todo,
        in_progress=in_progress,
        done=done,
        completion_rate=completion_rate,
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count,
        top_tags=top_tags,
        trend_labels=trend_labels,
        trend_data=trend_data
    )
