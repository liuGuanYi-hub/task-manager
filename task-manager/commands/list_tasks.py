"""列出任务命令"""
import click
from colorama import Fore, Style
from storage.json_storage import ANY_PROJECT
from storage.factory import create_storage as JSONStorage


@click.command()
@click.option("--status", "-s", type=click.Choice(["待办", "进行中", "已完成"]), help="按状态筛选")
@click.option("--priority", "-p", type=click.Choice(["低", "中", "高"]), help="按优先级筛选")
@click.option("--tag", "-t", help="按标签筛选")
@click.option("--project-id", type=int, help="只显示指定项目的任务")
@click.option("--no-project", is_flag=True, help="只显示未归属项目的任务")
def list_tasks(status: str = None, priority: str = None, tag: str = None, project_id: int = None, no_project: bool = False):
    """列出任务"""
    storage = JSONStorage()
    if project_id is not None and no_project:
        raise click.UsageError("--project-id 与 --no-project 不能同时使用")
    selected_project_id = None if no_project else project_id if project_id is not None else ANY_PROJECT
    tasks = storage.query(
        status=status,
        priority=priority,
        tag=tag,
        project_id=selected_project_id,
    )

    if not tasks:
        click.echo(f"{Fore.YELLOW}暂无任务{Style.RESET_ALL}")
        return

    click.echo(f"\n{Style.BRIGHT}📋 任务列表:{Style.RESET_ALL}\n")
    
    for task in tasks:
        click.echo(f"  [{task.id}] {task}")
        if task.description:
            click.echo(f"      {task.description}")
        if task.tags:
            click.echo(f"      标签：{', '.join(task.tags)}")
        if task.project_id is not None:
            project = storage.get_project_by_id(task.project_id)
            click.echo(f"      项目：{project.name if project else task.project_id}")
        click.echo()

    click.echo(f"{Style.DIM}共 {len(tasks)} 个任务{Style.RESET_ALL}\n")
