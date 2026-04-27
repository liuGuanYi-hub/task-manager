"""工具函数"""
from datetime import datetime, timedelta
from models.task import Task
from typing import List


def format_datetime(dt: datetime) -> str:
    """格式化日期时间"""
    if not dt:
        return ""
    return dt.strftime("%Y-%m-%d %H:%M")


def get_relative_time(dt: datetime) -> str:
    """获取相对时间描述"""
    if not dt:
        return ""
    
    now = datetime.now()
    diff = dt - now
    
    if diff.total_seconds() < 0:
        return "已过期"
    
    days = diff.days
    if days == 0:
        hours = diff.seconds // 3600
        if hours == 0:
            return "今天"
        elif hours < 24:
            return f"约{hours}小时后"
    elif days == 1:
        return "明天"
    elif days < 7:
        return f"{days}天后"
    elif days < 30:
        return f"{days // 7}周后"
    else:
        return f"{days // 30}个月后"


def check_due_tasks(tasks: List[Task], days: int = 3) -> List[Task]:
    """检查即将到期的任务"""
    now = datetime.now()
    deadline = now + timedelta(days=days)
    
    due_tasks = []
    for task in tasks:
        if task.due_date and now <= task.due_date <= deadline:
            due_tasks.append(task)
    
    return due_tasks


def check_overdue_tasks(tasks: List[Task]) -> List[Task]:
    """检查已过期的任务"""
    now = datetime.now()
    
    overdue_tasks = []
    for task in tasks:
        if task.due_date and task.due_date < now and task.status.value != "已完成":
            overdue_tasks.append(task)
    
    return overdue_tasks


def get_priority_color(priority_value: str) -> str:
    """获取优先级对应的颜色代码"""
    colors = {
        "高": "#dc3545",
        "中": "#ffc107",
        "低": "#28a745"
    }
    return colors.get(priority_value, "#666666")


def get_status_icon(status_value: str) -> str:
    """获取状态对应的图标"""
    icons = {
        "待办": "⬜",
        "进行中": "🔄",
        "已完成": "✅"
    }
    return icons.get(status_value, "⬜")


def get_priority_icon(priority_value: str) -> str:
    """获取优先级对应的图标"""
    icons = {
        "高": "🔴",
        "中": "🟡",
        "低": "🟢"
    }
    return icons.get(priority_value, "⚪")
