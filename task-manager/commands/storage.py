"""存储后端相关命令。"""

import click

from storage.sqlite_storage import SQLiteStorage


@click.command("migrate-sqlite")
@click.argument("json_path", default="tasks.json", required=False)
@click.option("--sqlite-path", default="tasks.db", show_default=True, help="目标 SQLite 文件")
@click.option(
    "--conflict",
    type=click.Choice(["remap", "skip", "replace"]),
    default="replace",
    show_default=True,
    help="重复 ID 的处理策略",
)
def migrate_sqlite(json_path: str, sqlite_path: str, conflict: str):
    """将 JSON 数据迁移到 SQLite；默认可重复执行。"""
    storage, result = SQLiteStorage.migrate_from_json(
        json_path,
        sqlite_path=sqlite_path,
        conflict=conflict,
    )
    click.echo(
        f"SQLite 迁移完成：任务 {result['tasks']} 个，"
        f"项目 {result['projects']} 个，视图 {result['saved_views']} 个"
    )
    click.echo(f"后端：{storage.backend_name}，文件：{storage.db_path}")
