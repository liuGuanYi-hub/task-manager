"""任务提醒功能"""
import click
from colorama import Fore, Style
from datetime import datetime
from storage.factory import create_storage as JSONStorage
from utils.helpers import check_due_tasks, check_overdue_tasks, get_relative_time


@click.command()
@click.option("--days", default=3, help="检查未来 N 天内到期的任务")
def remind(days: int):
    """显示任务提醒"""
    storage = JSONStorage()
    tasks = storage.get_all()
    
    # 检查过期任务
    overdue = check_overdue_tasks(tasks)
    if overdue:
        click.echo(f"\n{Fore.RED}{Style.BRIGHT}⚠️  已过期的任务:{Style.RESET_ALL}\n")
        for task in overdue:
            days_overdue = (datetime.now() - task.due_date).days
            click.echo(f"  {Fore.RED}[{task.id}] {task.title}{Style.RESET_ALL}")
            if task.description:
                click.echo(f"      {task.description}")
            click.echo(f"      已过期 {days_overdue} 天")
            click.echo()
    
    # 检查即将到期的任务
    due_soon = check_due_tasks(tasks, days)
    if due_soon:
        click.echo(f"\n{Fore.YELLOW}{Style.BRIGHT}⏰ 即将到期的任务（{days}天内）:{Style.RESET_ALL}\n")
        for task in due_soon:
            relative = get_relative_time(task.due_date)
            click.echo(f"  {Fore.YELLOW}[{task.id}] {task.title}{Style.RESET_ALL}")
            if task.description:
                click.echo(f"      {task.description}")
            click.echo(f"      截止时间：{task.due_date.strftime('%Y-%m-%d %H:%M')} ({relative})")
            click.echo()
    
    if not overdue and not due_soon:
        click.echo(f"\n{Fore.GREEN}✅ 太棒了！没有过期或即将到期的任务{Style.RESET_ALL}\n")
    else:
        total = len(overdue) + len(due_soon)
        click.echo(f"{Style.DIM}共 {total} 个任务需要关注{Style.RESET_ALL}\n")


@click.command()
def daily_summary():
    """每日摘要"""
    from models.task import Status
    from collections import Counter
    
    storage = JSONStorage()
    tasks = storage.get_all()
    
    click.echo(f"\n{Style.BRIGHT}📅 每日任务摘要{Style.RESET_ALL}\n")
    click.echo(f"日期：{datetime.now().strftime('%Y年%m月%d日 %A')}\n")
    
    # 统计
    status_count = Counter(task.status for task in tasks)
    todo = status_count.get(Status.TODO, 0)
    in_progress = status_count.get(Status.IN_PROGRESS, 0)
    done = status_count.get(Status.DONE, 0)
    
    click.echo(f"📊 今日概览:")
    click.echo(f"  待办：{todo}")
    click.echo(f"  进行中：{in_progress}")
    click.echo(f"  已完成：{done}")
    click.echo()
    
    # 高优先级待办
    high_priority = [t for t in tasks if t.priority.value == "高" and t.status != Status.DONE]
    if high_priority:
        click.echo(f"🔴 高优先级任务:")
        for task in high_priority:
            click.echo(f"  • {task.title}")
        click.echo()
    
    # 今天到期的任务
    today = datetime.now().replace(hour=23, minute=59, second=59)
    today_tasks = [t for t in tasks if t.due_date and t.due_date <= today and t.status != Status.DONE]
    if today_tasks:
        click.echo(f"⏰ 今天到期的任务:")
        for task in today_tasks:
            click.echo(f"  • {task.title}")
        click.echo()
    
    click.echo(f"{Style.DIM}祝您今天高效愉快！{Style.RESET_ALL}\n")


if __name__ == "__main__":
    # 测试提醒功能
    remind()
