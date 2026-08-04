"""更新任务命令"""
import click
from colorama import Fore, Style
from storage.json_storage import JSONStorage
from models.task import Priority, Status, parse_datetime


@click.command()
@click.argument("task_id", type=int)
@click.option("--title", "-t", help="新标题")
@click.option("--description", "-d", help="新描述")
@click.option("--priority", "-p", type=click.Choice(["低", "中", "高"]), help="新优先级")
@click.option("--status", "-s", type=click.Choice(["待办", "进行中", "已完成"]), help="新状态")
@click.option("--due-date", help="新截止时间，格式：YYYY-MM-DD 或 YYYY-MM-DD HH:MM；传空值可清除")
@click.option("--project-id", type=int, help="新的所属项目 ID")
@click.option("--clear-project", is_flag=True, help="清除任务的项目归属")
def update_task(task_id: int, title: str, description: str, priority: str, status: str, due_date: str, project_id: int, clear_project: bool):
    """更新任务"""
    storage = JSONStorage()
    task = storage.get_by_id(task_id)

    if not task:
        click.echo(f"{Fore.RED}❌ 任务不存在：ID {task_id}{Style.RESET_ALL}")
        return
    if project_id is not None and clear_project:
        raise click.UsageError("--project-id 与 --clear-project 不能同时使用")
    if project_id is not None and storage.get_project_by_id(project_id) is None:
        raise click.BadParameter(f"项目不存在：ID {project_id}", param_hint="--project-id")

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
    if due_date is not None:
        try:
            task.due_date = parse_datetime(due_date) if due_date else None
        except ValueError as exc:
            raise click.BadParameter("截止时间格式应为 YYYY-MM-DD 或 YYYY-MM-DD HH:MM", param_hint="--due-date") from exc
    if project_id is not None:
        task.project_id = project_id
    elif clear_project:
        task.project_id = None

    storage.update(task)
    
    click.echo(f"{Fore.GREEN}✅ 任务已更新：{Style.BRIGHT}{task.title}{Style.RESET_ALL}")
    click.echo(f"   状态：{task.status.value}")
    click.echo(f"   优先级：{task.priority.value}")
    if task.due_date:
        click.echo(f"   截止时间：{task.due_date.strftime('%Y-%m-%d %H:%M')}")
    if task.project_id is not None:
        click.echo(f"   项目 ID：{task.project_id}")
