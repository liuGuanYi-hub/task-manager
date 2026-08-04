"""删除任务命令"""
import click
from colorama import Fore, Style
from storage.factory import create_storage as JSONStorage


@click.command()
@click.argument("task_id", type=int)
@click.option("--confirm", "-y", is_flag=True, help="确认删除")
@click.option("--permanent", is_flag=True, help="永久删除，不可恢复")
def delete_task(task_id: int, confirm: bool, permanent: bool):
    """归档任务；使用 --permanent 才会永久删除。"""
    storage = JSONStorage()
    task = storage.get_by_id(task_id)

    if not task:
        click.echo(f"{Fore.RED}❌ 任务不存在：ID {task_id}{Style.RESET_ALL}")
        return

    action = "永久删除" if permanent else "归档"
    if not confirm:
        click.confirm(f"确定要{action}任务 '{task.title}' 吗？", abort=True)

    if permanent:
        storage.delete(task_id)
        click.echo(f"{Fore.GREEN}✅ 任务已永久删除：{task.title}{Style.RESET_ALL}")
    else:
        storage.archive(task_id)
        click.echo(f"{Fore.GREEN}✅ 任务已归档：{task.title}{Style.RESET_ALL}")
