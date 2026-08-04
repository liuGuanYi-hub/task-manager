"""JSON 数据存储"""
import json
from pathlib import Path
from datetime import datetime
from typing import Any, List, Optional, Sequence
from models.task import Task
from models.project import Project
from models.saved_view import SavedView
from models.task import parse_datetime


ANY_PROJECT = object()


class JSONStorage:
    """JSON 文件存储类"""

    def __init__(self, db_path: str = "tasks.json"):
        self.db_path = Path(db_path)
        self.tasks: List[Task] = []
        self.projects: List[Project] = []
        self.saved_views: List[SavedView] = []
        self.next_id = 1
        self.next_project_id = 1
        self.next_view_id = 1
        self._load()

    def _load(self):
        """从文件加载数据"""
        if self.db_path.exists():
            with open(self.db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.tasks = [Task.from_dict(t) for t in data.get("tasks", [])]
                self.projects = [Project.from_dict(p) for p in data.get("projects", [])]
                self.saved_views = [SavedView.from_dict(v) for v in data.get("saved_views", [])]
                self.next_id = data.get("next_id", 1)
                self.next_project_id = data.get("next_project_id", 1)
                self.next_view_id = data.get("next_view_id", 1)

                if self.tasks:
                    self.next_id = max(self.next_id, max((task.id or 0) for task in self.tasks) + 1)
                if self.projects:
                    self.next_project_id = max(
                        self.next_project_id,
                        max((project.id or 0) for project in self.projects) + 1,
                    )
                if self.saved_views:
                    self.next_view_id = max(
                        self.next_view_id,
                        max((view.id or 0) for view in self.saved_views) + 1,
                    )

    def _save(self):
        """保存数据到文件"""
        data = {
            "tasks": [t.to_dict() for t in self.tasks],
            "next_id": self.next_id,
            "projects": [p.to_dict() for p in self.projects],
            "next_project_id": self.next_project_id,
            "saved_views": [view.to_dict() for view in self.saved_views],
            "next_view_id": self.next_view_id,
        }
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add(self, task: Task) -> Task:
        """添加任务"""
        self._validate_project_id(task.project_id)
        task.id = self.next_id
        self.next_id += 1
        self.tasks.append(task)
        self._save()
        return task

    def get_all(self, include_archived: bool = False, project_id=ANY_PROJECT) -> List[Task]:
        """获取任务，默认隐藏已归档任务，可按项目或无项目筛选。"""
        if include_archived:
            tasks = self.tasks
        else:
            tasks = [task for task in self.tasks if not task.archived]

        if project_id is ANY_PROJECT:
            return tasks
        return [task for task in tasks if task.project_id == project_id]

    def query(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        tag: Optional[str] = None,
        include_archived: bool = False,
        sort_by: str = "created_at",
        reverse: bool = False,
        project_id=ANY_PROJECT,
        statuses: Optional[Sequence[str]] = None,
        due_date_from: Optional[datetime] = None,
        due_date_to: Optional[datetime] = None,
    ) -> List[Task]:
        """统一执行任务筛选和排序。"""
        tasks = self.get_all(include_archived=include_archived, project_id=project_id)
        status_values = set(statuses or [])
        if status:
            status_values.add(status)
        if status_values:
            tasks = [task for task in tasks if task.status.value in status_values]
        if priority:
            tasks = [task for task in tasks if task.priority.value == priority]
        if tag:
            tasks = [task for task in tasks if tag in task.tags]
        if due_date_from is not None:
            tasks = [task for task in tasks if task.due_date and task.due_date >= due_date_from]
        if due_date_to is not None:
            tasks = [task for task in tasks if task.due_date and task.due_date <= due_date_to]

        sortable_fields = {"id", "title", "created_at", "due_date", "updated_at", "completed_at"}
        if sort_by not in sortable_fields:
            raise ValueError(f"不支持的排序字段：{sort_by}")

        def sort_key(task: Task):
            value = getattr(task, sort_by)
            return (value is None, value, task.id or 0)

        return sorted(
            tasks,
            key=sort_key,
            reverse=reverse,
        )

    @staticmethod
    def _parse_view_datetime(value: Any, end_of_day: bool = False) -> Optional[datetime]:
        """解析保存视图的日期边界。"""
        if value in (None, ""):
            return None
        text = str(value).strip()
        try:
            parsed = parse_datetime(text)
        except ValueError as exc:
            raise ValueError(f"保存视图日期无效：{value}") from exc
        if parsed is not None and end_of_day and len(text) == 10:
            parsed = parsed.replace(hour=23, minute=59, second=59, microsecond=999999)
        return parsed

    def query_saved_view(self, view: SavedView) -> List[Task]:
        """按保存视图的筛选条件查询任务。"""
        filters = view.filters or {}
        project_value = filters.get("project_id", "all")
        if project_value in ("", "all"):
            project_id = ANY_PROJECT
        elif project_value == "none":
            project_id = None
        else:
            try:
                project_id = int(project_value)
            except (TypeError, ValueError) as exc:
                raise ValueError("保存视图项目筛选无效") from exc

        statuses = filters.get("statuses") or []
        if isinstance(statuses, str):
            statuses = [statuses]

        return self.query(
            priority=filters.get("priority") or None,
            tag=filters.get("tag") or None,
            include_archived=bool(filters.get("include_archived", False)),
            sort_by=filters.get("sort_by", "created_at"),
            reverse=bool(filters.get("reverse", False)),
            project_id=project_id,
            statuses=statuses,
            due_date_from=self._parse_view_datetime(filters.get("due_start")),
            due_date_to=self._parse_view_datetime(filters.get("due_end"), end_of_day=True),
        )

    def get_by_id(self, task_id: int) -> Optional[Task]:
        """根据 ID 获取任务"""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def update(self, task: Task) -> bool:
        """更新任务"""
        self._validate_project_id(task.project_id)
        for i, t in enumerate(self.tasks):
            if t.id == task.id:
                task.touch()
                self.tasks[i] = task
                self._save()
                return True
        return False

    def _validate_project_id(self, project_id: Optional[int]) -> None:
        """确保任务引用的项目存在，None 表示未归属项目。"""
        if project_id is not None and self.get_project_by_id(project_id) is None:
            raise ValueError(f"项目不存在：ID {project_id}")

    def add_project(self, project: Project) -> Project:
        """添加项目。"""
        project.id = self.next_project_id
        self.next_project_id += 1
        self.projects.append(project)
        self._save()
        return project

    def get_projects(self) -> List[Project]:
        """获取全部项目。"""
        return list(self.projects)

    def get_project_by_id(self, project_id: int) -> Optional[Project]:
        """根据 ID 获取项目。"""
        for project in self.projects:
            if project.id == project_id:
                return project
        return None

    def update_project(self, project: Project) -> bool:
        """更新项目。"""
        for i, current in enumerate(self.projects):
            if current.id == project.id:
                project.touch()
                self.projects[i] = project
                self._save()
                return True
        return False

    def add_saved_view(self, view: SavedView) -> SavedView:
        """添加保存视图。"""
        view.id = self.next_view_id
        self.next_view_id += 1
        self.saved_views.append(view)
        self._save()
        return view

    def get_saved_views(self) -> List[SavedView]:
        """获取保存视图。"""
        return list(self.saved_views)

    def get_saved_view_by_id(self, view_id: int) -> Optional[SavedView]:
        """根据 ID 获取保存视图。"""
        for view in self.saved_views:
            if view.id == view_id:
                return view
        return None

    def delete_saved_view(self, view_id: int) -> bool:
        """删除保存视图，不影响任务数据。"""
        for index, view in enumerate(self.saved_views):
            if view.id == view_id:
                del self.saved_views[index]
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
