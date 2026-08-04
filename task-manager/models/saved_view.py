"""保存视图模型定义。"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

from models.task import parse_datetime


@dataclass
class SavedView:
    """可重复使用的任务筛选视图。"""

    name: str
    filters: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    id: Optional[int] = None

    def touch(self, now: Optional[datetime] = None) -> None:
        """更新视图修改时间。"""
        self.updated_at = now or datetime.now()

    def to_dict(self) -> dict:
        """转换为 JSON 字典。"""
        return {
            "id": self.id,
            "name": self.name,
            "filters": self.filters,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SavedView":
        """从 JSON 字典创建保存视图。"""
        created_at = parse_datetime(data.get("created_at"), datetime.now()) or datetime.now()
        view_id: Optional[int] = data.get("id")
        if view_id is not None:
            try:
                view_id = int(view_id)
            except (TypeError, ValueError):
                view_id = None

        filters = data.get("filters", {})
        if not isinstance(filters, dict):
            filters = {}

        return cls(
            id=view_id,
            name=data.get("name", "未命名视图"),
            filters=filters,
            created_at=created_at,
            updated_at=parse_datetime(data.get("updated_at"), created_at) or created_at,
        )
