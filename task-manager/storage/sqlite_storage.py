"""SQLite 存储后端。

SQLiteStorage 保持 JSONStorage 的业务方法和数据模型不变，只替换持久化边界。
这样 CLI、页面、备份导入和 REST API 可以复用同一套业务规则。
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Any, List, Optional, Sequence, Tuple

from models.project import Project
from models.saved_view import SavedView
from models.task import Status, Task
from storage.json_storage import ANY_PROJECT, JSONStorage


class SQLiteStorage(JSONStorage):
    """使用 SQLite 文件保存任务、项目和保存视图。"""

    backend_name = "sqlite"

    def __init__(self, db_path: str = "tasks.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()
        self.tasks = []
        self.projects = []
        self.saved_views = []
        self.next_id = 1
        self.next_project_id = 1
        self.next_view_id = 1
        self._load()
        self._ensure_task_tags()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(str(self.db_path))
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize_database(self) -> None:
        connection = self._connect()
        try:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                INSERT OR IGNORE INTO metadata(key, value)
                    VALUES ('schema_version', '1');

                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    priority TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    due_date TEXT,
                    updated_at TEXT NOT NULL,
                    completed_at TEXT,
                    archived INTEGER NOT NULL DEFAULT 0,
                    tags_json TEXT NOT NULL DEFAULT '[]',
                    project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL
                );

                CREATE TABLE IF NOT EXISTS saved_views (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    filters_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS task_tags (
                    task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
                    tag TEXT NOT NULL,
                    PRIMARY KEY(task_id, tag)
                );

                CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
                CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id);
                CREATE INDEX IF NOT EXISTS idx_tasks_archived ON tasks(archived);
                CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date);
                CREATE INDEX IF NOT EXISTS idx_task_tags_tag_task ON task_tags(tag, task_id);
                """
            )
            connection.commit()
        finally:
            connection.close()

    @staticmethod
    def _task_from_row(row: sqlite3.Row) -> Task:
        return Task.from_dict(
            {
                "id": row["id"],
                "title": row["title"],
                "description": row["description"],
                "priority": row["priority"],
                "status": row["status"],
                "created_at": row["created_at"],
                "due_date": row["due_date"],
                "updated_at": row["updated_at"],
                "completed_at": row["completed_at"],
                "archived": bool(row["archived"]),
                "tags": json.loads(row["tags_json"] or "[]"),
                "project_id": row["project_id"],
            }
        )

    @staticmethod
    def _project_from_row(row: sqlite3.Row) -> Project:
        return Project.from_dict(
            {
                "id": row["id"],
                "name": row["name"],
                "description": row["description"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
        )

    @staticmethod
    def _view_from_row(row: sqlite3.Row) -> SavedView:
        return SavedView.from_dict(
            {
                "id": row["id"],
                "name": row["name"],
                "filters": json.loads(row["filters_json"] or "{}"),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
        )

    def _load(self) -> None:
        connection = self._connect()
        try:
            self.projects = [
                self._project_from_row(row)
                for row in connection.execute("SELECT * FROM projects ORDER BY id")
            ]
            self.tasks = [
                self._task_from_row(row)
                for row in connection.execute("SELECT * FROM tasks ORDER BY id")
            ]
            self.saved_views = [
                self._view_from_row(row)
                for row in connection.execute("SELECT * FROM saved_views ORDER BY id")
            ]
        finally:
            connection.close()

        self.next_id = max([task.id or 0 for task in self.tasks] + [0]) + 1
        self.next_project_id = max([project.id or 0 for project in self.projects] + [0]) + 1
        self.next_view_id = max([view.id or 0 for view in self.saved_views] + [0]) + 1

    def _ensure_task_tags(self) -> None:
        """为旧版只有 tags_json 的 SQLite 文件补建可查询的标签索引。"""
        tag_rows = [
            (task.id, tag)
            for task in self.tasks
            if task.id is not None
            for tag in task.tags
            if tag
        ]
        if not tag_rows:
            return

        connection = self._connect()
        try:
            indexed_count = connection.execute("SELECT COUNT(*) FROM task_tags").fetchone()[0]
            if indexed_count:
                return
            with connection:
                connection.executemany(
                    "INSERT INTO task_tags(task_id, tag) VALUES (?, ?)",
                    tag_rows,
                )
        finally:
            connection.close()

    def _save(self) -> None:
        connection = self._connect()
        try:
            with connection:
                connection.execute("DELETE FROM task_tags")
                connection.execute("DELETE FROM tasks")
                connection.execute("DELETE FROM saved_views")
                connection.execute("DELETE FROM projects")

                connection.executemany(
                    """
                    INSERT INTO projects(id, name, description, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            project.id,
                            project.name,
                            project.description,
                            project.created_at.isoformat(),
                            project.updated_at.isoformat(),
                        )
                        for project in self.projects
                    ],
                )
                connection.executemany(
                    """
                    INSERT INTO tasks(
                        id, title, description, priority, status, created_at,
                        due_date, updated_at, completed_at, archived, tags_json, project_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            task.id,
                            task.title,
                            task.description,
                            task.priority.value,
                            task.status.value,
                            task.created_at.isoformat(),
                            task.due_date.isoformat() if task.due_date else None,
                            task.updated_at.isoformat(),
                            task.completed_at.isoformat() if task.completed_at else None,
                            int(task.archived),
                            json.dumps(task.tags, ensure_ascii=False),
                            task.project_id,
                        )
                        for task in self.tasks
                    ],
                )
                connection.executemany(
                    "INSERT INTO task_tags(task_id, tag) VALUES (?, ?)",
                    [
                        (task.id, tag)
                        for task in self.tasks
                        if task.id is not None
                        for tag in task.tags
                        if tag
                    ],
                )
                connection.executemany(
                    """
                    INSERT INTO saved_views(id, name, filters_json, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            view.id,
                            view.name,
                            json.dumps(view.filters, ensure_ascii=False),
                            view.created_at.isoformat(),
                            view.updated_at.isoformat(),
                        )
                        for view in self.saved_views
                    ],
                )
        finally:
            connection.close()

    @staticmethod
    def _task_sort_sql(sort_by: str, reverse: bool) -> str:
        sort_columns = {
            "id": "tasks.id",
            "title": "tasks.title",
            "created_at": "tasks.created_at",
            "due_date": "tasks.due_date",
            "updated_at": "tasks.updated_at",
            "completed_at": "tasks.completed_at",
        }
        if sort_by not in sort_columns:
            raise ValueError(f"不支持的排序字段：{sort_by}")

        column = sort_columns[sort_by]
        if reverse:
            return (
                f"CASE WHEN {column} IS NULL THEN 0 ELSE 1 END ASC, "
                f"{column} DESC, tasks.id DESC"
            )
        return (
            f"CASE WHEN {column} IS NULL THEN 1 ELSE 0 END ASC, "
            f"{column} ASC, tasks.id ASC"
        )

    @staticmethod
    def _task_filter_sql(
        status: Optional[str] = None,
        priority: Optional[str] = None,
        tag: Optional[str] = None,
        include_archived: bool = False,
        project_id=ANY_PROJECT,
        statuses: Optional[Sequence[str]] = None,
        due_date_from: Optional[datetime] = None,
        due_date_to: Optional[datetime] = None,
    ) -> Tuple[str, List[Any]]:
        conditions = []
        params: List[Any] = []
        if not include_archived:
            conditions.append("tasks.archived = 0")

        if project_id is not ANY_PROJECT:
            if project_id is None:
                conditions.append("tasks.project_id IS NULL")
            else:
                conditions.append("tasks.project_id = ?")
                params.append(project_id)

        status_values = set(statuses or [])
        if status:
            status_values.add(status)
        if status_values:
            ordered_statuses = sorted(status_values)
            placeholders = ", ".join("?" for _ in ordered_statuses)
            conditions.append(f"tasks.status IN ({placeholders})")
            params.extend(ordered_statuses)

        if priority:
            conditions.append("tasks.priority = ?")
            params.append(priority)
        if tag:
            conditions.append(
                "EXISTS (SELECT 1 FROM task_tags "
                "WHERE task_tags.task_id = tasks.id AND task_tags.tag = ?)"
            )
            params.append(tag)
        if due_date_from is not None:
            conditions.append("tasks.due_date IS NOT NULL AND tasks.due_date >= ?")
            params.append(due_date_from.isoformat())
        if due_date_to is not None:
            conditions.append("tasks.due_date IS NOT NULL AND tasks.due_date <= ?")
            params.append(due_date_to.isoformat())

        return (" WHERE " + " AND ".join(conditions)) if conditions else "", params

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
        project_id=ANY_PROJECT,
        statuses: Optional[Sequence[str]] = None,
        due_date_from: Optional[datetime] = None,
        due_date_to: Optional[datetime] = None,
    ) -> Tuple[List[Task], int]:
        """在 SQLite 中完成过滤、计数、排序和分页，避免先加载全集。"""
        if offset < 0:
            raise ValueError("offset 不能小于 0")
        if limit < 1:
            raise ValueError("limit 必须大于 0")

        where_sql, params = self._task_filter_sql(
            status=status,
            priority=priority,
            tag=tag,
            include_archived=include_archived,
            project_id=project_id,
            statuses=statuses,
            due_date_from=due_date_from,
            due_date_to=due_date_to,
        )
        order_sql = self._task_sort_sql(sort_by, reverse)
        connection = self._connect()
        try:
            total = connection.execute(
                f"SELECT COUNT(*) FROM tasks{where_sql}",
                params,
            ).fetchone()[0]
            rows = connection.execute(
                f"SELECT tasks.* FROM tasks{where_sql} "
                f"ORDER BY {order_sql} LIMIT ? OFFSET ?",
                [*params, limit, offset],
            ).fetchall()
            return [self._task_from_row(row) for row in rows], total
        finally:
            connection.close()

    def get_projects_page(self, offset: int, limit: int) -> Tuple[List[Project], int]:
        """在 SQLite 中分页读取项目。"""
        if offset < 0:
            raise ValueError("offset 不能小于 0")
        if limit < 1:
            raise ValueError("limit 必须大于 0")
        connection = self._connect()
        try:
            total = connection.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
            rows = connection.execute(
                "SELECT * FROM projects ORDER BY id ASC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
            return [self._project_from_row(row) for row in rows], total
        finally:
            connection.close()

    def get_project_summary(self, project_id: int) -> dict:
        """用聚合查询返回项目任务统计，避免加载项目全部任务。"""
        connection = self._connect()
        try:
            row = connection.execute(
                """
                SELECT COUNT(*) AS total_tasks,
                       COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0)
                           AS completed_tasks
                FROM tasks
                WHERE project_id = ? AND archived = 0
                """,
                (Status.DONE.value, project_id),
            ).fetchone()
            return {
                "total_tasks": row["total_tasks"],
                "completed_tasks": row["completed_tasks"],
            }
        finally:
            connection.close()

    @classmethod
    def migrate_from_json(
        cls,
        json_path: str,
        sqlite_path: str = "tasks.db",
        conflict: str = "replace",
    ) -> Tuple["SQLiteStorage", dict]:
        """将 JSON 备份导入 SQLite；重复执行同一迁移不会重复已有 ID。"""
        with open(json_path, "r", encoding="utf-8") as handle:
            payload: Any = json.load(handle)
        storage = cls(sqlite_path)
        result = storage.import_payload(payload, conflict=conflict)
        return storage, result
