"""个人任务管理系统 - 主程序"""
import click
from colorama import init
from commands.create import create_task
from commands.list_tasks import list_tasks
from commands.update import update_task
from commands.delete import delete_task
from commands.search import search_tasks
from commands.stats import stats, weekly_report
from commands.remind import remind, daily_summary
from commands.projects import create_project, list_projects, update_project

# 初始化 colorama
init()


@click.group()
def cli():
    """个人任务管理系统 - 高效管理你的日常任务"""
    pass


# 注册命令
cli.add_command(create_task)
cli.add_command(list_tasks)
cli.add_command(update_task)
cli.add_command(delete_task)
cli.add_command(search_tasks)
cli.add_command(stats)
cli.add_command(weekly_report)
cli.add_command(remind)
cli.add_command(daily_summary)
cli.add_command(create_project)
cli.add_command(list_projects)
cli.add_command(update_project)


if __name__ == "__main__":
    cli()
