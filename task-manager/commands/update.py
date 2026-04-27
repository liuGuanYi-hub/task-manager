"""更新任务命令"""
import click
from colorama import Fore, Style
from storage.json_storage import JSONStorage
from models.task import Task, Priority, Status


@click.command()
@click.argument("task_id", type=int)
@click.option("--title", "-t", help="新标题")
@click.option("--description", "-d", help="新描述")
@click.option("--priority", "-p", type=click.Choice(["低", "中", "高"]), help="新优先级")
@click.option("--status", "-s", type=click.Choice(["待办", "进行中", "已完成"]), help="新状态")
def update_task(task_id: int, title: str, description: str, priority: str, status: str):
    """更新任务"""
    storage = JSONStorage()
    task = storage.get_by_id(task_id)

    if not task:
        click.echo(f"{Fore.RED}❌ 任务不存在：ID {task_id}{Style.RESET_ALL}")
        return

    # 更新字段
    if title:
        task.title = title
    if description:
        task.description = description
    if priority:
        priority_map = {"低": Priority.LOW, "中": Priority.MEDIUM, "高": Priority.HIGH}
        task.priority = priority_map[priority]
    if status:
        status_map = {"待办": Status.TODO, "进行中": Status.IN_PROGRESS, "已完成": Status.DONE}
        task.status = status_map[status]

    storage.update(task)
    
    click.echo(f"{Fore.GREEN}✅ 任务已更新：{Style.BRIGHT}{task.title}{Style.RESET_ALL}")
    click.echo(f"   状态：{task.status.value}")
    click.echo(f"   优先级：{task.priority.value}")
