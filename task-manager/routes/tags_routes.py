"""标签管理路由"""
from flask import Blueprint, render_template
from storage.factory import create_storage as JSONStorage
from collections import Counter

tags_bp = Blueprint("tags", __name__, url_prefix="/stats/tags")


@tags_bp.route("/")
def tags_page():
    """标签管理页面"""
    storage = JSONStorage()
    tasks = storage.get_all()

    all_tags = []
    for task in tasks:
        all_tags.extend(task.tags)

    tags = Counter(all_tags).most_common(20)
    colors = [
        "#4f7cff", "#8b5cf6", "#f093fb", "#f5576c",
        "#4facfe", "#00f2fe", "#43e97b", "#38f9d7",
        "#fa709a", "#fee140", "#30cfd0", "#330867",
    ]

    return render_template("tags.html", tags=tags, colors=colors)
