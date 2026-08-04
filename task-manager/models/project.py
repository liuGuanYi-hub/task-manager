"""项目模型定义"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from models.task import parse_datetime


@dataclass
class Project:
    """轻量项目实体，任务通过 project_id 与项目建立关联。"""

    name: str
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    id: Optional[int] = None

    def touch(self, now: Optional[datetime] = None) -> None:
        """更新项目的修改时间。"""
        self.updated_at = now or datetime.now()

    def to_dict(self) -> dict:
        """转换为 JSON 字典。"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Project":
        """从 JSON 字典创建项目。"""
        created_at = parse_datetime(data.get("created_at"), datetime.now()) or datetime.now()
        project_id: Optional[int] = data.get("id")
        if project_id is not None:
            try:
                project_id = int(project_id)
            except (TypeError, ValueError):
                project_id = None

        return cls(
            id=project_id,
            name=data["name"],
            description=data.get("description", ""),
            created_at=created_at,
            updated_at=parse_datetime(data.get("updated_at"), created_at) or created_at,
        )
