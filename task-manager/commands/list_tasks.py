"""列出任务命令"""
import click
from colorama import Fore, Style
from storage.json_storage import JSONStorage


@click.command()
@click.option("--status", "-s", type=click.Choice(["待办", "进行中", "已完成"]), help="按状态筛选")
@click.option("--priority", "-p", type=click.Choice(["低", "中", "高"]), help="按优先级筛选")
@click.option("--tag", "-t", help="按标签筛选")
def list_tasks(status: str = None, priority: str = None, tag: str = None):
    """列出任务"""
    storage = JSONStorage()
    tasks = storage.query(status=status, priority=priority, tag=tag)

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
        click.echo()

    click.echo(f"{Style.DIM}共 {len(tasks)} 个任务{Style.RESET_ALL}\n")
