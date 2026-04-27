"""任务模型测试"""
import pytest
from datetime import datetime
from models.task import Task, Priority, Status


def test_create_task():
    """测试创建任务"""
    task = Task(title="测试任务")
    assert task.title == "测试任务"
    assert task.priority == Priority.MEDIUM
    assert task.status == Status.TODO
    assert task.id is None


def test_task_with_description():
    """测试带描述的任务"""
    task = Task(title="测试", description="这是一个测试任务")
    assert task.description == "这是一个测试任务"


def test_task_priority():
    """测试任务优先级"""
    task = Task(title="测试", priority=Priority.HIGH)
    assert task.priority == Priority.HIGH
    assert task.priority.value == "高"


def test_task_status():
    """测试任务状态"""
    task = Task(title="测试")
    assert task.status == Status.TODO
    
    task.status = Status.IN_PROGRESS
    assert task.status == Status.IN_PROGRESS
    assert task.status.value == "进行中"


def test_task_to_dict():
    """测试任务转换为字典"""
    task = Task(
        title="测试任务",
        description="测试描述",
        priority=Priority.HIGH,
        tags=["测试", "学习"]
    )
    task.id = 1
    
    data = task.to_dict()
    
    assert data["id"] == 1
    assert data["title"] == "测试任务"
    assert data["description"] == "测试描述"
    assert data["priority"] == "高"
    assert data["status"] == "待办"
    assert data["tags"] == ["测试", "学习"]
    assert "created_at" in data
    assert "due_date" in data


def test_task_from_dict():
    """测试从字典创建任务"""
    data = {
        "id": 1,
        "title": "测试任务",
        "description": "测试描述",
        "priority": "高",
        "status": "进行中",
        "created_at": "2024-01-01T00:00:00",
        "due_date": None,
        "tags": ["测试"]
    }
    
    task = Task.from_dict(data)
    
    assert task.id == 1
    assert task.title == "测试任务"
    assert task.priority == Priority.HIGH
    assert task.status == Status.IN_PROGRESS
    assert task.tags == ["测试"]


def test_task_str():
    """测试任务字符串表示"""
    task = Task(title="测试任务", priority=Priority.HIGH)
    result = str(task)
    assert "测试任务" in result
    assert "🔴" in result  # 高优先级图标


def test_task_with_tags():
    """测试带标签的任务"""
    task = Task(title="测试", tags=["学习", "Python", "编程"])
    assert len(task.tags) == 3
    assert "学习" in task.tags
    assert "Python" in task.tags


def test_task_with_due_date():
    """测试带截止日期的任务"""
    due_date = datetime(2024, 12, 31, 23, 59, 59)
    task = Task(title="测试", due_date=due_date)
    assert task.due_date == due_date
    
    # 测试转换为字典
    data = task.to_dict()
    assert data["due_date"] == "2024-12-31T23:59:59"
