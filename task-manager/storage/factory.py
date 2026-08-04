"""按环境变量创建存储后端。"""

import os
from typing import Optional

from storage.interface import StorageProtocol
from storage.json_storage import JSONStorage
from storage.sqlite_storage import SQLiteStorage


def create_storage(db_path: Optional[str] = None) -> StorageProtocol:
    """创建当前配置的存储。

    默认继续使用 tasks.json；设置 TASK_MANAGER_STORAGE=sqlite 后使用 tasks.db。
    路径可分别通过 TASK_MANAGER_JSON_PATH/TASK_MANAGER_SQLITE_PATH 覆盖。
    """
    backend = os.getenv("TASK_MANAGER_STORAGE", "json").strip().lower()
    if backend not in {"json", "sqlite"}:
        raise ValueError("TASK_MANAGER_STORAGE 只能是 json 或 sqlite")

    if db_path is not None:
        selected_path = db_path
    elif backend == "sqlite":
        selected_path = os.getenv("TASK_MANAGER_SQLITE_PATH", "tasks.db")
    else:
        selected_path = os.getenv("TASK_MANAGER_JSON_PATH", "tasks.json")

    if backend == "sqlite":
        return SQLiteStorage(selected_path)
    return JSONStorage(selected_path)
