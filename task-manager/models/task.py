"""任务模型定义"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List


class Priority(Enum):
    """任务优先级"""
    LOW = "低"
    MEDIUM = "中"
    HIGH = "高"


class Status(Enum):
    """任务状态"""
    TODO = "待办"
    IN_PROGRESS = "进行中"
    DONE = "已完成"


@dataclass
class Task:
    """任务类"""
    title: str
    description: str = ""
    priority: Priority = Priority.MEDIUM
    status: Status = Status.TODO
    created_at: datetime = field(default_factory=datetime.now)
    due_date: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    id: Optional[int] = None

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "tags": self.tags
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """从字典创建任务"""
        return cls(
            id=data.get("id"),
            title=data["title"],
            description=data.get("description", ""),
            priority=Priority(data.get("priority", "中")),
            status=Status(data.get("status", "待办")),
            created_at=datetime.fromisoformat(data["created_at"]),
            due_date=datetime.fromisoformat(data["due_date"]) if data.get("due_date") else None,
            tags=data.get("tags", [])
        )

    def __str__(self) -> str:
        status_icon = {
            Status.TODO: "⬜",
            Status.IN_PROGRESS: "🔄",
            Status.DONE: "✅"
        }
        priority_icon = {
            Priority.LOW: "🟢",
            Priority.MEDIUM: "🟡",
            Priority.HIGH: "🔴"
        }
        return f"{status_icon[self.status]} {priority_icon[self.priority]} {self.title}"
