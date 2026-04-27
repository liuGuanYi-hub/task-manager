"""创建任务命令"""
import click
from colorama import Fore, Style
from models.task import Task, Priority
from storage.json_storage import JSONStorage


@click.command()
@click.argument("title")
@click.option("--description", "-d", default="", help="任务描述")
@click.option("--priority", "-p", type=click.Choice(["低", "中", "高"]), default="中", help="任务优先级")
@click.option("--tag", "-t", multiple=True, help="任务标签（可多次使用）")
def create_task(title: str, description: str, priority: str, tag: tuple):
    """创建新任务"""
    storage = JSONStorage()
    
    priority_map = {"低": Priority.LOW, "中": Priority.MEDIUM, "高": Priority.HIGH}
    task = Task(
        title=title,
        description=description,
        priority=priority_map[priority],
        tags=list(tag)
    )
    
    created = storage.add(task)
    
    click.echo(f"{Fore.GREEN}✅ 任务已创建：{Style.BRIGHT}{created.title}{Style.RESET_ALL}")
    click.echo(f"   ID: {created.id}")
    click.echo(f"   优先级：{created.priority.value}")
    if created.tags:
        click.echo(f"   标签：{', '.join(created.tags)}")
