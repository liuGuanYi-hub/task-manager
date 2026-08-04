"""项目管理命令"""
import click
from colorama import Fore, Style

from models.project import Project
from storage.json_storage import JSONStorage


@click.command("create-project")
@click.argument("name")
@click.option("--description", "-d", default="", help="项目描述")
def create_project(name: str, description: str):
    """创建项目。"""
    name = name.strip()
    if not name:
        raise click.BadParameter("项目名称不能为空", param_hint="name")

    project = JSONStorage().add_project(Project(name=name, description=description))
    click.echo(f"{Fore.GREEN}✅ 项目已创建：{Style.BRIGHT}{project.name}{Style.RESET_ALL}")
    click.echo(f"   ID: {project.id}")


@click.command("list-projects")
def list_projects():
    """列出项目。"""
    projects = JSONStorage().get_projects()
    if not projects:
        click.echo(f"{Fore.YELLOW}暂无项目{Style.RESET_ALL}")
        return

    click.echo(f"\n{Style.BRIGHT}📁 项目列表:{Style.RESET_ALL}\n")
    for project in projects:
        click.echo(f"  [{project.id}] {project.name}")
        if project.description:
            click.echo(f"      {project.description}")
    click.echo(f"\n{Style.DIM}共 {len(projects)} 个项目{Style.RESET_ALL}\n")


@click.command("update-project")
@click.argument("project_id", type=int)
@click.option("--name", "name", help="新项目名称")
@click.option("--description", "description", help="新项目描述")
def update_project(project_id: int, name: str, description: str):
    """更新项目。"""
    storage = JSONStorage()
    project = storage.get_project_by_id(project_id)
    if project is None:
        click.echo(f"{Fore.RED}❌ 项目不存在：ID {project_id}{Style.RESET_ALL}")
        return

    if name is not None:
        name = name.strip()
        if not name:
            raise click.BadParameter("项目名称不能为空", param_hint="--name")
        project.name = name
    if description is not None:
        project.description = description

    storage.update_project(project)
    click.echo(f"{Fore.GREEN}✅ 项目已更新：{Style.BRIGHT}{project.name}{Style.RESET_ALL}")
