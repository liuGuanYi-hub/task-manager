"""JSON 数据存储"""
import copy
import json
import os
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Any, List, Optional, Sequence
from models.task import Task
from models.project import Project
from models.saved_view import SavedView
from models.task import parse_datetime


ANY_PROJECT = object()


class ImportValidationError(ValueError):
    """导入数据校验失败。"""


class JSONStorage:
    """JSON 文件存储类"""

    backend_name = "json"

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
        data = self._data_payload()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=self.db_path.parent,
                prefix=f".{self.db_path.name}.",
                suffix=".tmp",
                delete=False,
            ) as handle:
                temp_path = Path(handle.name)
                json.dump(data, handle, ensure_ascii=False, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, self.db_path)
            temp_path = None
        finally:
            if temp_path is not None and temp_path.exists():
                temp_path.unlink()

    def _data_payload(self) -> dict:
        """生成应用数据，不包含导出时间等备份元数据。"""
        return {
            "tasks": [t.to_dict() for t in self.tasks],
            "next_id": self.next_id,
            "projects": [p.to_dict() for p in self.projects],
            "next_project_id": self.next_project_id,
            "saved_views": [view.to_dict() for view in self.saved_views],
            "next_view_id": self.next_view_id,
        }

    def export_payload(self, include_archived: bool = True) -> dict:
        """生成完整导出/备份数据。"""
        data = self._data_payload()
        if not include_archived:
            data["tasks"] = [task.to_dict() for task in self.get_all()]
        data["schema_version"] = 1
        data["export_date"] = datetime.now().isoformat()
        data["total_tasks"] = len(data["tasks"])
        data["total_projects"] = len(data["projects"])
        data["total_saved_views"] = len(data["saved_views"])
        return data
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

    @staticmethod
    def _validate_import_records(payload: Any):
        """校验并解析导入记录，不修改当前存储。"""
        if not isinstance(payload, dict):
            raise ImportValidationError("导入文件必须是 JSON 对象")
        if payload.get("schema_version", 1) not in (1, "1"):
            raise ImportValidationError("不支持的备份版本")

        parsed = {}
        for key, parser in (
            ("projects", Project.from_dict),
            ("tasks", Task.from_dict),
            ("saved_views", SavedView.from_dict),
        ):
            records = payload.get(key, [])
            if not isinstance(records, list):
                raise ImportValidationError(f"字段 {key} 必须是数组")
            parsed[key] = []
            ids = set()
            for index, record in enumerate(records):
                if not isinstance(record, dict):
                    raise ImportValidationError(f"字段 {key}[{index}] 必须是对象")
                try:
                    item = parser(record)
                except (KeyError, TypeError, ValueError) as exc:
                    raise ImportValidationError(f"字段 {key}[{index}] 格式无效") from exc
                if record.get("id") is not None and item.id is None:
                    raise ImportValidationError(f"字段 {key}[{index}] 的 ID 无效")
                if key == "tasks" and (not isinstance(item.title, str) or not item.title.strip()):
                    raise ImportValidationError(f"字段 tasks[{index}] 缺少有效标题")
                if key == "tasks" and not isinstance(item.tags, list):
                    raise ImportValidationError(f"字段 tasks[{index}] 的标签必须是数组")
                if key == "tasks" and record.get("project_id") is not None and item.project_id is None:
                    raise ImportValidationError(f"字段 tasks[{index}] 的项目 ID 无效")
                if key == "projects" and (not isinstance(item.name, str) or not item.name.strip()):
                    raise ImportValidationError(f"字段 projects[{index}] 缺少有效名称")
                if key == "saved_views" and (not isinstance(item.name, str) or not item.name.strip()):
                    raise ImportValidationError(f"字段 saved_views[{index}] 缺少有效名称")
                if key == "saved_views" and not isinstance(record.get("filters", {}), dict):
                    raise ImportValidationError(f"字段 saved_views[{index}] 的筛选条件必须是对象")
                if item.id is not None:
                    if item.id <= 0 or item.id in ids:
                        raise ImportValidationError(f"字段 {key} 存在重复或无效 ID")
                    ids.add(item.id)
                parsed[key].append(item)

        existing_project_ids = {project.id for project in parsed["projects"] if project.id is not None}
        for index, task in enumerate(parsed["tasks"]):
            if task.project_id is not None and task.project_id not in existing_project_ids:
                # 当前项目中的已有项目在 import_payload 中会再次校验。
                continue
            if task.project_id is not None and task.project_id <= 0:
                raise ImportValidationError(f"字段 tasks[{index}] 的项目 ID 无效")
        return parsed

    @staticmethod
    def _next_available_id(used_ids: set, start: int) -> int:
        """获取不冲突的正整数 ID。"""
        candidate = max(start, 1)
        while candidate in used_ids:
            candidate += 1
        used_ids.add(candidate)
        return candidate

    def import_payload(self, payload: Any, conflict: str = "remap") -> dict:
        """校验并导入数据，默认对冲突 ID 重映射，写入失败时回滚内存状态。"""
        if conflict not in {"remap", "skip", "replace"}:
            raise ImportValidationError("冲突策略必须是 remap、skip 或 replace")

        parsed = self._validate_import_records(payload)
        current_project_ids = {project.id for project in self.projects if project.id is not None}
        current_task_ids = {task.id for task in self.tasks if task.id is not None}
        current_view_ids = {view.id for view in self.saved_views if view.id is not None}
        incoming_project_ids = {project.id for project in parsed["projects"] if project.id is not None}
        known_project_ids = current_project_ids | incoming_project_ids

        for index, task in enumerate(parsed["tasks"]):
            if task.project_id is not None and task.project_id not in known_project_ids:
                raise ImportValidationError(f"字段 tasks[{index}] 引用了不存在的项目")
        for index, view in enumerate(parsed["saved_views"]):
            project_id = (view.filters or {}).get("project_id")
            if isinstance(project_id, str) and project_id.isdigit():
                project_id = int(project_id)
            if isinstance(project_id, int) and project_id not in known_project_ids:
                raise ImportValidationError(f"字段 saved_views[{index}] 引用了不存在的项目")

        new_projects = []
        project_map = {}
        skipped_projects = set()
        used_project_ids = set(current_project_ids)
        next_project_id = max(self.next_project_id, max(used_project_ids or {0}) + 1)
        for project in parsed["projects"]:
            old_id = project.id
            if old_id is None:
                project.id = self._next_available_id(used_project_ids, next_project_id)
                next_project_id = project.id + 1
            elif old_id in current_project_ids:
                if conflict == "skip":
                    skipped_projects.add(old_id)
                    project_map[old_id] = old_id
                    continue
                if conflict == "remap":
                    project.id = self._next_available_id(used_project_ids, next_project_id)
                    next_project_id = project.id + 1
                else:
                    used_project_ids.add(old_id)
                project_map[old_id] = project.id
            else:
                used_project_ids.add(old_id)
                project_map[old_id] = old_id
            new_projects.append(project)

        new_tasks = []
        task_map = {}
        skipped_tasks = 0
        remapped_tasks = 0
        used_task_ids = set(current_task_ids)
        next_task_id = max(self.next_id, max(used_task_ids or {0}) + 1)
        for task in parsed["tasks"]:
            old_id = task.id
            if task.project_id in project_map:
                task.project_id = project_map[task.project_id]
            if old_id is None:
                task.id = self._next_available_id(used_task_ids, next_task_id)
                next_task_id = task.id + 1
            elif old_id in current_task_ids:
                if conflict == "skip":
                    skipped_tasks += 1
                    task_map[old_id] = old_id
                    continue
                if conflict == "remap":
                    task.id = self._next_available_id(used_task_ids, next_task_id)
                    next_task_id = task.id + 1
                    remapped_tasks += 1
                else:
                    used_task_ids.add(old_id)
                task_map[old_id] = task.id
            else:
                used_task_ids.add(old_id)
                task_map[old_id] = old_id
            new_tasks.append(task)

        new_views = []
        skipped_views = 0
        remapped_views = 0
        used_view_ids = set(current_view_ids)
        next_view_id = max(self.next_view_id, max(used_view_ids or {0}) + 1)
        for view in parsed["saved_views"]:
            filters = copy.deepcopy(view.filters or {})
            project_id = filters.get("project_id")
            if isinstance(project_id, str) and project_id.isdigit():
                project_id = int(project_id)
            if project_id in project_map:
                filters["project_id"] = project_map[project_id]
            view.filters = filters

            old_id = view.id
            if old_id is None:
                view.id = self._next_available_id(used_view_ids, next_view_id)
                next_view_id = view.id + 1
            elif old_id in current_view_ids:
                if conflict == "skip":
                    skipped_views += 1
                    continue
                if conflict == "remap":
                    view.id = self._next_available_id(used_view_ids, next_view_id)
                    next_view_id = view.id + 1
                    remapped_views += 1
                else:
                    used_view_ids.add(old_id)
            else:
                used_view_ids.add(old_id)
            new_views.append(view)

        snapshot = (
            copy.deepcopy(self.tasks),
            copy.deepcopy(self.projects),
            copy.deepcopy(self.saved_views),
            self.next_id,
            self.next_project_id,
            self.next_view_id,
        )
        try:
            replace_project_ids = {project.id for project in new_projects if project.id in current_project_ids}
            replace_task_ids = {task.id for task in new_tasks if task.id in current_task_ids}
            replace_view_ids = {view.id for view in new_views if view.id in current_view_ids}
            if conflict == "replace":
                self.projects = [project for project in self.projects if project.id not in replace_project_ids]
                self.tasks = [task for task in self.tasks if task.id not in replace_task_ids]
                self.saved_views = [view for view in self.saved_views if view.id not in replace_view_ids]
            self.projects.extend(new_projects)
            self.tasks.extend(new_tasks)
            self.saved_views.extend(new_views)
            self.next_id = max([task.id or 0 for task in self.tasks] + [1]) + 1
            self.next_project_id = max([project.id or 0 for project in self.projects] + [1]) + 1
            self.next_view_id = max([view.id or 0 for view in self.saved_views] + [1]) + 1
            self._save()
        except Exception:
            (
                self.tasks,
                self.projects,
                self.saved_views,
                self.next_id,
                self.next_project_id,
                self.next_view_id,
            ) = snapshot
            raise

        return {
            "projects": len(new_projects),
            "tasks": len(new_tasks),
            "saved_views": len(new_views),
            "skipped_tasks": skipped_tasks,
            "skipped_projects": len(skipped_projects),
            "skipped_views": skipped_views,
            "remapped_tasks": remapped_tasks,
            "remapped_views": remapped_views,
            "conflict": conflict,
        }

    def preview_import(self, payload: Any, conflict: str = "remap") -> dict:
        """只读预览导入结果，复用正式导入逻辑但不写入当前文件。"""
        current_ids = {
            "tasks": {task.id for task in self.tasks if task.id is not None},
            "projects": {project.id for project in self.projects if project.id is not None},
            "saved_views": {view.id for view in self.saved_views if view.id is not None},
        }
        incoming_counts = {}
        conflicts = {}
        if isinstance(payload, dict):
            for key in ("tasks", "projects", "saved_views"):
                records = payload.get(key, [])
                records = records if isinstance(records, list) else []
                incoming_counts[key] = len(records)
                incoming_ids = {
                    record.get("id")
                    for record in records
                    if isinstance(record, dict) and record.get("id") is not None
                }
                conflicts[key] = len(incoming_ids & current_ids[key])

        preview_storage = copy.deepcopy(self)
        preview_storage._save = lambda: None
        result = preview_storage.import_payload(payload, conflict=conflict)
        result["preview"] = True
        result["incoming"] = incoming_counts
        result["conflicts"] = conflicts
        result["current"] = {
            "tasks": len(self.tasks),
            "projects": len(self.projects),
            "saved_views": len(self.saved_views),
        }
        result["after"] = {
            "tasks": len(preview_storage.tasks),
            "projects": len(preview_storage.projects),
            "saved_views": len(preview_storage.saved_views),
        }
        return result

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
        """永久删除任务，仅供显式维护操作使用。"""
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
