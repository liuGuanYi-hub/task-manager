"""JSON 数据存储"""
import json
from pathlib import Path
from typing import List, Optional
from models.task import Task


class JSONStorage:
    """JSON 文件存储类"""

    def __init__(self, db_path: str = "tasks.json"):
        self.db_path = Path(db_path)
        self.tasks: List[Task] = []
        self.next_id = 1
        self._load()

    def _load(self):
        """从文件加载数据"""
        if self.db_path.exists():
            with open(self.db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.tasks = [Task.from_dict(t) for t in data.get("tasks", [])]
                self.next_id = data.get("next_id", 1)

    def _save(self):
        """保存数据到文件"""
        data = {
            "tasks": [t.to_dict() for t in self.tasks],
            "next_id": self.next_id
        }
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add(self, task: Task) -> Task:
        """添加任务"""
        task.id = self.next_id
        self.next_id += 1
        self.tasks.append(task)
        self._save()
        return task

    def get_all(self, include_archived: bool = False) -> List[Task]:
        """获取任务，默认隐藏已归档任务。"""
        if include_archived:
            return self.tasks
        return [task for task in self.tasks if not task.archived]

    def query(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        tag: Optional[str] = None,
        include_archived: bool = False,
        sort_by: str = "created_at",
        reverse: bool = False,
    ) -> List[Task]:
        """统一执行任务筛选和排序。"""
        tasks = self.get_all(include_archived=include_archived)
        if status:
            tasks = [task for task in tasks if task.status.value == status]
        if priority:
            tasks = [task for task in tasks if task.priority.value == priority]
        if tag:
            tasks = [task for task in tasks if tag in task.tags]

        sortable_fields = {"id", "title", "created_at", "due_date", "updated_at", "completed_at"}
        if sort_by not in sortable_fields:
            raise ValueError(f"不支持的排序字段：{sort_by}")

        def sort_key(task: Task):
            value = getattr(task, sort_by)
            return (value is None, value)

        return sorted(
            tasks,
            key=sort_key,
            reverse=reverse,
        )

    def get_by_id(self, task_id: int) -> Optional[Task]:
        """根据 ID 获取任务"""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def update(self, task: Task) -> bool:
        """更新任务"""
        for i, t in enumerate(self.tasks):
            if t.id == task.id:
                task.touch()
                self.tasks[i] = task
                self._save()
                return True
        return False

    def archive(self, task_id: int) -> bool:
        """归档任务，保留数据但从默认列表隐藏。"""
        task = self.get_by_id(task_id)
        if task is None or task.archived:
            return False
        task.archived = True
        task.touch()
        self._save()
        return True

    def restore(self, task_id: int) -> bool:
        """恢复已归档任务。"""
        task = self.get_by_id(task_id)
        if task is None or not task.archived:
            return False
        task.archived = False
        task.touch()
        self._save()
        return True

    def get_archived(self) -> List[Task]:
        """获取已归档任务。"""
        return [task for task in self.tasks if task.archived]

    def delete(self, task_id: int) -> bool:
        """删除任务"""
        for i, task in enumerate(self.tasks):
            if task.id == task_id:
                del self.tasks[i]
                self._save()
                return True
        return False

    def clear(self):
        """清空所有任务"""
        self.tasks = []
        self._save()
