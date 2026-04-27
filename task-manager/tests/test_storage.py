"""存储模块测试"""
import pytest
import os
import json
from models.task import Task, Priority, Status
from storage.json_storage import JSONStorage


@pytest.fixture
def test_storage():
    """创建测试存储"""
    test_db = "test_tasks.json"
    storage = JSONStorage(test_db)
    storage.clear()
    yield storage
    # 清理测试文件
    if os.path.exists(test_db):
        os.remove(test_db)


def test_add_task(test_storage):
    """测试添加任务"""
    task = Task(title="测试任务")
    created = test_storage.add(task)
    
    assert created.id == 1
    assert created.title == "测试任务"
    assert test_storage.next_id == 2


def test_get_all_tasks(test_storage):
    """测试获取所有任务"""
    task1 = Task(title="任务 1")
    task2 = Task(title="任务 2")
    
    test_storage.add(task1)
    test_storage.add(task2)
    
    all_tasks = test_storage.get_all()
    assert len(all_tasks) == 2
    assert all_tasks[0].title == "任务 1"
    assert all_tasks[1].title == "任务 2"


def test_get_by_id(test_storage):
    """测试根据 ID 获取任务"""
    task = Task(title="测试任务")
    test_storage.add(task)
    
    retrieved = test_storage.get_by_id(1)
    assert retrieved is not None
    assert retrieved.title == "测试任务"
    
    # 测试不存在的 ID
    not_found = test_storage.get_by_id(999)
    assert not_found is None


def test_update_task(test_storage):
    """测试更新任务"""
    task = Task(title="原任务", priority=Priority.MEDIUM)
    test_storage.add(task)
    
    # 更新任务
    task.title = "新任务"
    task.priority = Priority.HIGH
    test_storage.update(task)
    
    # 验证更新
    updated = test_storage.get_by_id(1)
    assert updated.title == "新任务"
    assert updated.priority == Priority.HIGH


def test_delete_task(test_storage):
    """测试删除任务"""
    task = Task(title="待删除任务")
    test_storage.add(task)
    
    # 删除任务
    result = test_storage.delete(1)
    assert result is True
    
    # 验证删除
    deleted = test_storage.get_by_id(1)
    assert deleted is None
    assert len(test_storage.get_all()) == 0


def test_delete_nonexistent_task(test_storage):
    """测试删除不存在的任务"""
    result = test_storage.delete(999)
    assert result is False


def test_clear_all_tasks(test_storage):
    """测试清空所有任务"""
    task1 = Task(title="任务 1")
    task2 = Task(title="任务 2")
    
    test_storage.add(task1)
    test_storage.add(task2)
    
    test_storage.clear()
    
    all_tasks = test_storage.get_all()
    assert len(all_tasks) == 0


def test_persistence(test_storage):
    """测试数据持久化"""
    task = Task(title="持久化测试", priority=Priority.HIGH)
    test_storage.add(task)
    
    # 创建新的存储实例（模拟重新加载）
    new_storage = JSONStorage(test_storage.db_path)
    
    tasks = new_storage.get_all()
    assert len(tasks) == 1
    assert tasks[0].title == "持久化测试"
    assert tasks[0].priority == Priority.HIGH


def test_auto_save_on_add(test_storage):
    """测试添加任务时自动保存"""
    task = Task(title="自动保存测试")
    test_storage.add(task)
    
    # 检查文件是否存在
    assert test_storage.db_path.exists()
    
    # 读取文件内容
    with open(test_storage.db_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["title"] == "自动保存测试"


def test_auto_save_on_update(test_storage):
    """测试更新任务时自动保存"""
    task = Task(title="更新测试")
    test_storage.add(task)
    
    task.title = "已更新"
    test_storage.update(task)
    
    # 读取文件内容
    with open(test_storage.db_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data["tasks"][0]["title"] == "已更新"


def test_auto_save_on_delete(test_storage):
    """测试删除任务时自动保存"""
    task = Task(title="删除测试")
    test_storage.add(task)
    
    test_storage.delete(1)
    
    # 读取文件内容
    with open(test_storage.db_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert len(data["tasks"]) == 0
