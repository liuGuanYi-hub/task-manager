"""设置页面路由"""
from flask import Blueprint, render_template, send_file
from storage.json_storage import JSONStorage
import csv
import json
import io
from datetime import datetime
from pathlib import Path

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


@settings_bp.route("/")
def settings_page():
    """设置页面"""
    storage = JSONStorage()
    tasks = storage.get_all()

    db_path = Path(storage.db_path)
    if db_path.exists():
        file_size = f"{db_path.stat().st_size / 1024:.2f} KB"
        last_modified = datetime.fromtimestamp(db_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    else:
        file_size = "0 KB"
        last_modified = "无数据"

    return render_template(
        "settings.html",
        total_tasks=len(tasks),
        file_size=file_size,
        last_modified=last_modified,
    )


@settings_bp.route("/export/<format>")
def export_data(format):
    """导出数据"""
    storage = JSONStorage()
    tasks = storage.get_all()

    if format == "json":
        data = {
            "export_date": datetime.now().isoformat(),
            "total_tasks": len(tasks),
            "tasks": [task.to_dict() for task in tasks],
        }
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        return send_file(
            io.BytesIO(json_str.encode("utf-8")),
            mimetype="application/json",
            as_attachment=True,
            download_name=f"tasks_export_{datetime.now().strftime('%Y%m%d')}.json",
        )

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "标题", "描述", "优先级", "状态", "创建时间", "截止时间", "标签"])

        for task in tasks:
            writer.writerow(
                [
                    task.id,
                    task.title,
                    task.description,
                    task.priority.value,
                    task.status.value,
                    task.created_at.strftime("%Y-%m-%d"),
                    task.due_date.strftime("%Y-%m-%d") if task.due_date else "",
                    ", ".join(task.tags),
                ]
            )

        csv_content = output.getvalue()
        return send_file(
            io.BytesIO(csv_content.encode("utf-8-sig")),
            mimetype="text/csv",
            as_attachment=True,
            download_name=f"tasks_export_{datetime.now().strftime('%Y%m%d')}.csv",
        )

    return "不支持的格式", 400
