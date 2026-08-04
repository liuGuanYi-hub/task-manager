"""归档任务管理路由。"""
from flask import Blueprint, redirect, render_template, url_for

from storage.factory import create_storage as JSONStorage


archive_bp = Blueprint("archive", __name__, url_prefix="/archive")


@archive_bp.route("")
@archive_bp.route("/")
def archived_tasks():
    """查看已归档任务。"""
    storage = JSONStorage()
    return render_template("archived.html", tasks=storage.get_archived())


@archive_bp.route("/<int:task_id>/restore", methods=["POST"])
def restore_task(task_id: int):
    """恢复归档任务。"""
    storage = JSONStorage()
    if not storage.restore(task_id):
        return "归档任务不存在", 404
    return redirect(url_for("archive.archived_tasks"))
