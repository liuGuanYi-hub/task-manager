"""SQLite 存储后端。

SQLiteStorage 保持 JSONStorage 的业务方法和数据模型不变，只替换持久化边界。
这样 CLI、页面、备份导入和 REST API 可以复用同一套业务规则。
"""

import json
import sqlite3
from pathlib import Path
from typing import Any, Tuple

from models.project import Project
from models.saved_view import SavedView
from models.task import Task
from storage.json_storage import JSONStorage


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

                CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
                CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id);
                CREATE INDEX IF NOT EXISTS idx_tasks_archived ON tasks(archived);
                CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date);
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

    def _save(self) -> None:
        connection = self._connect()
        try:
            with connection:
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
