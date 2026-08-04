"""创建任务命令"""
import click
from colorama import Fore, Style
from models.task import Task, Priority, parse_datetime
from storage.json_storage import JSONStorage


@click.command()
@click.argument("title")
@click.option("--description", "-d", default="", help="任务描述")
@click.option("--priority", "-p", type=click.Choice(["低", "中", "高"]), default="中", help="任务优先级")
@click.option("--tag", "-t", multiple=True, help="任务标签（可多次使用）")
@click.option("--due-date", help="截止时间，格式：YYYY-MM-DD 或 YYYY-MM-DD HH:MM")
@click.option("--project-id", type=int, help="所属项目 ID")
def create_task(title: str, description: str, priority: str, tag: tuple, due_date: str, project_id: int):
    """创建新任务"""
    storage = JSONStorage()

    if project_id is not None and storage.get_project_by_id(project_id) is None:
        raise click.BadParameter(f"项目不存在：ID {project_id}", param_hint="--project-id")
    
    priority_map = {"低": Priority.LOW, "中": Priority.MEDIUM, "高": Priority.HIGH}
    try:
        parsed_due_date = parse_datetime(due_date) if due_date else None
    except ValueError as exc:
        raise click.BadParameter("截止时间格式应为 YYYY-MM-DD 或 YYYY-MM-DD HH:MM", param_hint="--due-date") from exc

    task = Task(
        title=title,
        description=description,
        priority=priority_map[priority],
        due_date=parsed_due_date,
        tags=list(tag),
        project_id=project_id,
    )
    
    created = storage.add(task)
    
    click.echo(f"{Fore.GREEN}✅ 任务已创建：{Style.BRIGHT}{created.title}{Style.RESET_ALL}")
    click.echo(f"   ID: {created.id}")
    click.echo(f"   优先级：{created.priority.value}")
    if created.tags:
        click.echo(f"   标签：{', '.join(created.tags)}")
    if created.due_date:
        click.echo(f"   截止时间：{created.due_date.strftime('%Y-%m-%d %H:%M')}")
    if created.project_id is not None:
        click.echo(f"   项目 ID：{created.project_id}")
