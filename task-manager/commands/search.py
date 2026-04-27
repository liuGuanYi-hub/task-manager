"""搜索任务命令"""
import click
from colorama import Fore, Style
from storage.json_storage import JSONStorage
from models.task import Task


@click.command()
@click.argument("keyword")
@click.option("--title", is_flag=True, help="只在标题中搜索")
@click.option("--description", is_flag=True, help="只在描述中搜索")
@click.option("--tag", is_flag=True, help="只在标签中搜索")
@click.option("--all", "search_all", is_flag=True, help="在所有字段中搜索（默认）")
def search_tasks(keyword: str, title: bool, description: bool, tag: bool, search_all: bool):
    """搜索任务"""
    storage = JSONStorage()
    tasks = storage.get_all()
    
    # 确定搜索范围
    if not any([title, description, tag, search_all]):
        search_all = True
    
    results = []
    keyword_lower = keyword.lower()
    
    for task in tasks:
        match = False
        
        if search_all:
            # 在所有字段中搜索
            if (keyword_lower in task.title.lower() or 
                keyword_lower in task.description.lower() or
                any(keyword_lower in t.lower() for t in task.tags)):
                match = True
        else:
            # 在指定字段中搜索
            if title and keyword_lower in task.title.lower():
                match = True
            if description and keyword_lower in task.description.lower():
                match = True
            if tag and any(keyword_lower in t.lower() for t in task.tags):
                match = True
        
        if match:
            results.append(task)
    
    if not results:
        click.echo(f"{Fore.YELLOW}未找到匹配 '{keyword}' 的任务{Style.RESET_ALL}")
        return
    
    click.echo(f"\n{Style.BRIGHT}🔍 搜索结果：'{keyword}'{Style.RESET_ALL}\n")
    
    for task in results:
        click.echo(f"  [{task.id}] {task}")
        if task.description:
            click.echo(f"      {task.description}")
        if task.tags:
            click.echo(f"      标签：{', '.join(task.tags)}")
        click.echo()
    
    click.echo(f"{Style.DIM}找到 {len(results)} 个匹配的任务{Style.RESET_ALL}\n")
