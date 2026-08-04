"""设置页面路由"""
from flask import Blueprint, render_template, request, send_file, url_for
from storage.json_storage import ImportValidationError
from storage.factory import create_storage as JSONStorage
import csv
import json
import io
from datetime import datetime
from pathlib import Path

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


def _render_settings(storage: JSONStorage, import_error=None, import_success=None):
    """构造设置页面，统一展示数据和导入结果。"""
    db_path = Path(storage.db_path)
    if db_path.exists():
        file_size = f"{db_path.stat().st_size / 1024:.2f} KB"
        last_modified = datetime.fromtimestamp(db_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    else:
        file_size = "0 KB"
        last_modified = "无数据"

    return render_template(
        "settings.html",
        total_tasks=len(storage.get_all()),
        total_archived=len(storage.get_archived()),
        total_projects=len(storage.get_projects()),
        file_size=file_size,
        last_modified=last_modified,
        import_error=import_error,
        import_success=import_success,
    )


@settings_bp.route("/")
def settings_page():
    """设置页面"""
    return _render_settings(
        JSONStorage(),
        import_success=request.args.get("imported"),
    )


@settings_bp.route("/export/<format>")
def export_data(format):
    """导出数据"""
    storage = JSONStorage()
    tasks = storage.get_all(include_archived=True)

    if format == "json":
        data = storage.export_payload(include_archived=True)
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
        writer.writerow([
            "ID", "标题", "描述", "优先级", "状态", "创建时间", "截止时间",
            "更新时间", "完成时间", "已归档", "项目 ID", "项目名称", "标签",
        ])

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
                    task.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
                    task.completed_at.strftime("%Y-%m-%d %H:%M:%S") if task.completed_at else "",
                    "是" if task.archived else "否",
                    task.project_id or "",
                    storage.get_project_by_id(task.project_id).name if task.project_id and storage.get_project_by_id(task.project_id) else "",
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


@settings_bp.route("/backup")
@settings_bp.route("/backup/json")
def backup_data():
    """下载包含归档任务、项目和保存视图的完整备份。"""
    storage = JSONStorage()
    data = storage.export_payload(include_archived=True)
    data["backup"] = True
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    return send_file(
        io.BytesIO(json_str.encode("utf-8")),
        mimetype="application/json",
        as_attachment=True,
        download_name=f"task_manager_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
    )


@settings_bp.route("/import", methods=["POST"])
def import_data():
    """导入 JSON 备份，校验失败时保持现有数据不变。"""
    storage = JSONStorage()
    uploaded = request.files.get("backup_file")
    if uploaded is None or not uploaded.filename:
        return _render_settings(storage, import_error="请选择 JSON 备份文件"), 400

    raw = uploaded.read(5 * 1024 * 1024 + 1)
    if len(raw) > 5 * 1024 * 1024:
        return _render_settings(storage, import_error="导入文件不能超过 5 MB"), 400

    try:
        payload = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return _render_settings(storage, import_error="导入文件不是有效的 UTF-8 JSON"), 400

    conflict = request.form.get("conflict", "remap")
    try:
        result = storage.import_payload(payload, conflict=conflict)
    except ImportValidationError as exc:
        return _render_settings(storage, import_error=str(exc)), 400
    except (OSError, TypeError, ValueError) as exc:
        return _render_settings(storage, import_error=f"导入失败，原数据未改变：{exc}"), 400

    summary = f"导入完成：任务 {result['tasks']} 个，项目 {result['projects']} 个，视图 {result['saved_views']} 个"
    return redirect(url_for("settings.settings_page", imported=summary))
