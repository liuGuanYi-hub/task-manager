"""任务模型定义"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional, List


def parse_datetime(value: Any, default: Optional[datetime] = None) -> Optional[datetime]:
    """统一解析任务日期，并将带时区时间转换为本地无时区时间。"""
    if value is None or value == "":
        return default

    if isinstance(value, datetime):
        parsed = value
    else:
        text = str(value).strip()
        if text.endswith("Z"):
            text = f"{text[:-1]}+00:00"
        parsed = datetime.fromisoformat(text)

    if parsed.tzinfo is not None:
        parsed = parsed.astimezone().replace(tzinfo=None)
    return parsed


def parse_bool(value: Any, default: bool = False) -> bool:
    """兼容 JSON 中的布尔值和历史字符串值。"""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "是"}
    return bool(value)


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
    updated_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    archived: bool = False
    tags: List[str] = field(default_factory=list)
    id: Optional[int] = None

    def touch(self, now: Optional[datetime] = None) -> None:
        """更新时间，并根据状态维护完成时间。"""
        self.updated_at = now or datetime.now()
        if self.status == Status.DONE:
            if self.completed_at is None:
                self.completed_at = self.updated_at
        else:
            self.completed_at = None

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
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "archived": self.archived,
            "tags": self.tags
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """从字典创建任务"""
        created_at = parse_datetime(data.get("created_at"), datetime.now()) or datetime.now()
        return cls(
            id=data.get("id"),
            title=data["title"],
            description=data.get("description", ""),
            priority=Priority(data.get("priority", "中")),
            status=Status(data.get("status", "待办")),
            created_at=created_at,
            due_date=parse_datetime(data.get("due_date")),
            updated_at=parse_datetime(data.get("updated_at"), created_at) or created_at,
            completed_at=parse_datetime(data.get("completed_at")),
            archived=parse_bool(data.get("archived"), False),
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
