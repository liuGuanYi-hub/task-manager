"""删除任务命令"""
import click
from colorama import Fore, Style
from storage.json_storage import JSONStorage


@click.command()
@click.argument("task_id", type=int)
@click.option("--confirm", "-y", is_flag=True, help="确认删除")
def delete_task(task_id: int, confirm: bool):
    """删除任务"""
    storage = JSONStorage()
    task = storage.get_by_id(task_id)

    if not task:
        click.echo(f"{Fore.RED}❌ 任务不存在：ID {task_id}{Style.RESET_ALL}")
        return

    if not confirm:
        click.confirm(f"确定要删除任务 '{task.title}' 吗？", abort=True)

    storage.delete(task_id)
    click.echo(f"{Fore.GREEN}✅ 任务已删除：{task.title}{Style.RESET_ALL}")
