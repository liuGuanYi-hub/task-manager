"""存储层公共接口。

CLI、Flask 页面和 REST API 只依赖这组方法，不直接依赖具体的文件或数据库实现。
"""

from datetime import datetime
from typing import Any, List, Optional, Protocol, Sequence, Tuple

from models.project import Project
from models.saved_view import SavedView
from models.task import Task


class StorageProtocol(Protocol):
    """任务管理存储后端需要提供的最小业务接口。"""

    db_path: Any
    backend_name: str

    def add(self, task: Task) -> Task: ...

    def get_all(self, include_archived: bool = False, project_id: Any = ...) -> List[Task]: ...

    def get_by_id(self, task_id: int) -> Optional[Task]: ...

    def update(self, task: Task) -> bool: ...

    def query(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        tag: Optional[str] = None,
        include_archived: bool = False,
        sort_by: str = "created_at",
        reverse: bool = False,
        project_id: Any = ...,
        statuses: Optional[Sequence[str]] = None,
        due_date_from: Optional[datetime] = None,
        due_date_to: Optional[datetime] = None,
    ) -> List[Task]: ...

    def query_page(
        self,
        offset: int,
        limit: int,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        tag: Optional[str] = None,
        include_archived: bool = False,
        sort_by: str = "created_at",
        reverse: bool = False,
        project_id: Any = ...,
        statuses: Optional[Sequence[str]] = None,
        due_date_from: Optional[datetime] = None,
        due_date_to: Optional[datetime] = None,
    ) -> Tuple[List[Task], int]: ...

    def archive(self, task_id: int) -> bool: ...

    def restore(self, task_id: int) -> bool: ...

    def get_archived(self) -> List[Task]: ...

    def add_project(self, project: Project) -> Project: ...

    def get_projects(self) -> List[Project]: ...

    def get_project_by_id(self, project_id: int) -> Optional[Project]: ...

    def update_project(self, project: Project) -> bool: ...

    def add_saved_view(self, view: SavedView) -> SavedView: ...

    def get_saved_views(self) -> List[SavedView]: ...

    def get_saved_view_by_id(self, view_id: int) -> Optional[SavedView]: ...

    def delete_saved_view(self, view_id: int) -> bool: ...

    def export_payload(self, include_archived: bool = True) -> dict: ...

    def import_payload(self, payload: Any, conflict: str = "remap") -> dict: ...
