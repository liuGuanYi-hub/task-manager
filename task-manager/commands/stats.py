"""统计报表命令"""
import click
from colorama import Fore, Style
from storage.factory import create_storage as JSONStorage
from models.task import Status, Priority
from collections import Counter


@click.command()
@click.option("--detail", is_flag=True, help="显示详细统计")
def stats(detail: bool):
    """显示任务统计信息"""
    storage = JSONStorage()
    tasks = storage.get_all()
    
    if not tasks:
        click.echo(f"{Fore.YELLOW}暂无任务数据{Style.RESET_ALL}")
        return
    
    total = len(tasks)
    
    # 按状态统计
    status_count = Counter(task.status for task in tasks)
    todo_count = status_count.get(Status.TODO, 0)
    in_progress_count = status_count.get(Status.IN_PROGRESS, 0)
    done_count = status_count.get(Status.DONE, 0)
    
    # 按优先级统计
    priority_count = Counter(task.priority for task in tasks)
    high_count = priority_count.get(Priority.HIGH, 0)
    medium_count = priority_count.get(Priority.MEDIUM, 0)
    low_count = priority_count.get(Priority.LOW, 0)
    
    # 完成率
    completion_rate = (done_count / total * 100) if total > 0 else 0
    
    # 标签统计
    all_tags = []
    for task in tasks:
        all_tags.extend(task.tags)
    tag_count = Counter(all_tags)
    
    click.echo(f"\n{Style.BRIGHT}📊 任务统计报表{Style.RESET_ALL}\n")
    click.echo(f"{Style.BRIGHT}总体概况:{Style.RESET_ALL}")
    click.echo(f"  总任务数：{total}")
    click.echo(f"  完成率：{completion_rate:.1f}%")
    click.echo()
    
    click.echo(f"{Style.BRIGHT}按状态:{Style.RESET_ALL}")
    click.echo(f"  ⬜ 待办：{todo_count}")
    click.echo(f"  🔄 进行中：{in_progress_count}")
    click.echo(f"  ✅ 已完成：{done_count}")
    click.echo()
    
    click.echo(f"{Style.BRIGHT}按优先级:{Style.RESET_ALL}")
    click.echo(f"  🔴 高优先级：{high_count}")
    click.echo(f"  🟡 中优先级：{medium_count}")
    click.echo(f"  🟢 低优先级：{low_count}")
    click.echo()
    
    if detail and tag_count:
        click.echo(f"{Style.BRIGHT}热门标签:{Style.RESET_ALL}")
        for tag, count in tag_count.most_common(5):
            click.echo(f"  #{tag}: {count}")
        click.echo()
    
    # 进度条
    bar_length = 30
    filled = int(bar_length * done_count / total) if total > 0 else 0
    bar = "█" * filled + "░" * (bar_length - filled)
    click.echo(f"{Style.BRIGHT}进度:{Style.RESET_ALL} [{bar}] {done_count}/{total}")
    click.echo()


@click.command()
@click.option("--days", default=7, help="显示最近 N 天的任务")
def weekly_report(days: int):
    """生成周报"""
    from datetime import datetime, timedelta
    
    storage = JSONStorage()
    tasks = storage.get_all()
    
    # 计算日期范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # 筛选日期范围内的任务
    filtered_tasks = []
    for task in tasks:
        if start_date <= task.created_at <= end_date:
            filtered_tasks.append(task)
    
    if not filtered_tasks:
        click.echo(f"{Fore.YELLOW}最近 {days} 天没有创建任务{Style.RESET_ALL}")
        return
    
    click.echo(f"\n{Style.BRIGHT}📈 周报（最近 {days} 天）{Style.RESET_ALL}\n")
    click.echo(f"  创建任务数：{len(filtered_tasks)}")
    
    # 按状态统计
    status_count = Counter(task.status for task in filtered_tasks)
    click.echo(f"  完成任务数：{status_count.get(Status.DONE, 0)}")
    click.echo(f"  进行中：{status_count.get(Status.IN_PROGRESS, 0)}")
    click.echo(f"  待办：{status_count.get(Status.TODO, 0)}")
    click.echo()
