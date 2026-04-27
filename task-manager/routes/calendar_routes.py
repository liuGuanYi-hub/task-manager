"""日历视图路由"""
from flask import Blueprint, render_template_string, request, jsonify
from storage.json_storage import JSONStorage
from models.task import Task, Status
from datetime import datetime, timedelta
from calendar import monthrange

calendar_bp = Blueprint('calendar', __name__, url_prefix='/calendar')

# 日历页面模板
CALENDAR_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>任务日历 - 任务管理系统</title>
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
        .calendar-controls {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 30px;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
        }
        .month-nav {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        .month-nav button {
            padding: 10px 20px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
        }
        .month-nav button:hover {
            background: #5568d3;
        }
        .month-title {
            font-size: 1.5em;
            font-weight: bold;
            color: #495057;
        }
        .view-toggle {
            display: flex;
            gap: 10px;
        }
        .view-toggle button {
            padding: 8px 16px;
            background: white;
            border: 2px solid #667eea;
            color: #667eea;
            border-radius: 5px;
            cursor: pointer;
        }
        .view-toggle button.active {
            background: #667eea;
            color: white;
        }
        .calendar-content {
            padding: 30px;
        }
        .calendar-grid {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 10px;
        }
        .weekday-header {
            text-align: center;
            padding: 15px;
            font-weight: bold;
            color: #6c757d;
            background: #f8f9fa;
            border-radius: 5px;
        }
        .day-cell {
            min-height: 120px;
            border: 1px solid #e9ecef;
            border-radius: 10px;
            padding: 10px;
            background: white;
            cursor: pointer;
            transition: all 0.3s;
        }
        .day-cell:hover {
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            transform: translateY(-2px);
        }
        .day-cell.today {
            border: 2px solid #667eea;
            background: #f0f4ff;
        }
        .day-cell.has-tasks {
            background: #f8f9fa;
        }
        .day-number {
            font-weight: bold;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .day-number .date {
            font-size: 1.2em;
        }
        .task-dots {
            display: flex;
            gap: 3px;
            margin-top: 5px;
            flex-wrap: wrap;
        }
        .task-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
        }
        .task-dot.high { background: #dc3545; }
        .task-dot.medium { background: #ffc107; }
        .task-dot.low { background: #28a745; }
        .task-count {
            font-size: 0.8em;
            color: #6c757d;
            margin-top: 5px;
        }
        .empty-day {
            background: #f8f9fa;
            border: 1px dashed #e9ecef;
        }
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 1000;
        }
        .modal.show {
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .modal-content {
            background: white;
            border-radius: 15px;
            padding: 30px;
            max-width: 600px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
        }
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #e9ecef;
        }
        .modal-header h2 {
            color: #495057;
        }
        .close-btn {
            background: none;
            border: none;
            font-size: 1.5em;
            cursor: pointer;
            color: #6c757d;
        }
        .task-list-modal {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .task-item-modal {
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        .task-item-modal.done {
            border-left-color: #28a745;
            opacity: 0.7;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📅 任务日历</h1>
            <p>按日期查看和管理任务</p>
        </div>
        <div class="nav">
            <a href="/">📋 任务列表</a>
            <a href="/stats">📊 统计仪表板</a>
            <a href="/calendar" class="active">📅 日历视图</a>
            <a href="/projects">📁 项目管理</a>
            <a href="/settings">⚙️ 设置</a>
        </div>
        <div class="calendar-controls">
            <div class="month-nav">
                <button onclick="changeMonth(-1)">◀ 上月</button>
                <div class="month-title">{{ month_title }}</div>
                <button onclick="changeMonth(1)">下月 ▶</button>
            </div>
            <div class="view-toggle">
                <button class="active">月视图</button>
                <button onclick="location.href='/calendar/week'">周视图</button>
            </div>
        </div>
        <div class="calendar-content">
            <div class="calendar-grid">
                <div class="weekday-header">周一</div>
                <div class="weekday-header">周二</div>
                <div class="weekday-header">周三</div>
                <div class="weekday-header">周四</div>
                <div class="weekday-header">周五</div>
                <div class="weekday-header">周六</div>
                <div class="weekday-header">周日</div>
                
                {% for day in days %}
                {% if day.is_empty %}
                <div class="day-cell empty-day"></div>
                {% else %}
                <div class="day-cell {{ 'today' if day.is_today else '' }} {{ 'has-tasks' if day.task_count > 0 else '' }}" 
                     onclick="showDayTasks('{{ day.date }}')">
                    <div class="day-number">
                        <span class="date">{{ day.day }}</span>
                    </div>
                    {% if day.task_count > 0 %}
                    <div class="task-dots">
                        {% for priority in day.priorities %}
                        <div class="task-dot {{ priority }}"></div>
                        {% endfor %}
                    </div>
                    <div class="task-count">{{ day.task_count }} 个任务</div>
                    {% endif %}
                </div>
                {% endif %}
                {% endfor %}
            </div>
        </div>
    </div>

    <div id="dayModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 id="modalTitle">任务列表</h2>
                <button class="close-btn" onclick="closeModal()">×</button>
            </div>
            <div id="taskList" class="task-list-modal"></div>
        </div>
    </div>

    <script>
        const tasksByDate = {{ tasks_json | tojson }};
        
        function changeMonth(delta) {
            const url = new URL(window.location.href);
            const current = new Date(url.searchParams.get('date') || '{{ today }}');
            current.setMonth(current.getMonth() + delta);
            url.searchParams.set('date', current.toISOString());
            window.location.href = url.toString();
        }

        function showDayTasks(date) {
            const modal = document.getElementById('dayModal');
            const taskList = document.getElementById('taskList');
            const modalTitle = document.getElementById('modalTitle');
            
            const tasks = tasksByDate[date] || [];
            modalTitle.textContent = date + ' 的任务 (' + tasks.length + '个)';
            
            if (tasks.length === 0) {
                taskList.innerHTML = '<p style="text-align:center;color:#6c757d;padding:40px;">暂无任务</p>';
            } else {
                taskList.innerHTML = tasks.map(task => `
                    <div class="task-item-modal ${task.status_class}">
                        <strong>${task.title}</strong>
                        <p style="color:#6c757d;margin:5px 0;">${task.description || ''}</p>
                        <div style="display:flex;gap:10px;margin-top:10px;">
                            <span style="font-size:0.9em;">${task.priority_icon} ${task.priority}</span>
                            <span style="font-size:0.9em;">${task.status_icon} ${task.status}</span>
                        </div>
                    </div>
                `).join('');
            }
            
            modal.classList.add('show');
        }

        function closeModal() {
            document.getElementById('dayModal').classList.remove('show');
        }

        // 点击模态框外部关闭
        document.getElementById('dayModal').addEventListener('click', function(e) {
            if (e.target === this) {
                closeModal();
            }
        });
    </script>
</body>
</html>
"""


@calendar_bp.route('/')
def calendar_view():
    """日历视图"""
    from urllib.parse import parse_qs
    
    storage = JSONStorage()
    tasks = storage.get_all()
    
    # 获取当前月份
    query_string = request.query_string.decode()
    params = parse_qs(query_string)
    
    if 'date' in params:
        current_date = datetime.fromisoformat(params['date'][0])
    else:
        current_date = datetime.now()
    
    year = current_date.year
    month = current_date.month
    
    # 获取月份信息
    first_weekday, days_in_month = monthrange(year, month)
    # 调整为周一为第一天（Python 中周一=0）
    first_weekday = (first_weekday - 1) % 7
    
    # 生成月份标题
    month_title = current_date.strftime('%Y年%m月')
    
    # 准备日期数据
    days = []
    
    # 添加空白单元格
    for i in range(first_weekday):
        days.append({'is_empty': True})
    
    # 添加日期
    today = datetime.now().date()
    for day in range(1, days_in_month + 1):
        date = datetime(year, month, day)
        date_str = date.strftime('%Y-%m-%d')
        
        # 筛选当天的任务
        day_tasks = [t for t in tasks if t.created_at.date() == date.date()]
        
        # 获取优先级分布
        priorities = []
        for task in day_tasks:
            if task.priority.value == '高':
                priorities.append('high')
            elif task.priority.value == '中':
                priorities.append('medium')
            else:
                priorities.append('low')
        
        days.append({
            'is_empty': False,
            'day': day,
            'date': date_str,
            'is_today': date.date() == today,
            'task_count': len(day_tasks),
            'priorities': priorities
        })
    
    # 准备任务数据（用于模态框）
    tasks_json = {}
    for day in days:
        if not day.get('is_empty'):
            date_str = day['date']
            day_tasks = [t for t in tasks if t.created_at.date() == datetime.fromisoformat(date_str).date()]
            tasks_json[date_str] = [
                {
                    'title': t.title,
                    'description': t.description,
                    'priority': t.priority.value,
                    'priority_icon': '🔴' if t.priority.value == '高' else '🟡' if t.priority.value == '中' else '🟢',
                    'status': t.status.value,
                    'status_icon': '✅' if t.status.value == '已完成' else '🔄' if t.status.value == '进行中' else '⬜',
                    'status_class': 'done' if t.status.value == '已完成' else ''
                }
                for t in day_tasks
            ]
    
    return render_template_string(
        CALENDAR_TEMPLATE,
        month_title=month_title,
        days=days,
        today=datetime.now().isoformat(),
        tasks_json=tasks_json
    )
