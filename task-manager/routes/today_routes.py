"""Today 工作台 UI 预览路由。"""

from datetime import date

from flask import Blueprint, render_template


today_bp = Blueprint("today", __name__, url_prefix="/today")

_WEEKDAYS = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]


def _demo_sections():
    """返回只用于界面预览的演示分组，不读写任务数据。"""
    return [
        {
            "key": "today",
            "eyebrow": "TODAY",
            "title": "今天要做",
            "subtitle": "把注意力放在当前最重要的事情上",
            "count": 3,
            "accent": "blue",
            "tasks": [
                {
                    "title": "完成项目首页 UI",
                    "priority": "高优先级",
                    "priority_class": "high",
                    "meta": "截止今天 18:00",
                    "tag": "项目",
                    "completed": False,
                },
                {
                    "title": "整理 API 接口文档",
                    "priority": "中优先级",
                    "priority_class": "medium",
                    "meta": "进行中 · 已投入 45 分钟",
                    "tag": "开发",
                    "completed": False,
                },
                {
                    "title": "更新本周学习计划",
                    "priority": "低优先级",
                    "priority_class": "low",
                    "meta": "今天安排 · 预计 20 分钟",
                    "tag": "学习",
                    "completed": True,
                },
            ],
        },
        {
            "key": "overdue",
            "eyebrow": "OVERDUE",
            "title": "已逾期",
            "subtitle": "先处理一个最容易完成的任务",
            "count": 2,
            "accent": "rose",
            "tasks": [
                {
                    "title": "补充阶段计划文档",
                    "priority": "高优先级",
                    "priority_class": "high",
                    "meta": "逾期 1 天",
                    "tag": "计划",
                    "completed": False,
                },
                {
                    "title": "清理未归档任务",
                    "priority": "中优先级",
                    "priority_class": "medium",
                    "meta": "逾期 2 天",
                    "tag": "整理",
                    "completed": False,
                },
            ],
        },
        {
            "key": "upcoming",
            "eyebrow": "UPCOMING",
            "title": "接下来",
            "subtitle": "提前看一眼，给未来留出空间",
            "count": 2,
            "accent": "mint",
            "tasks": [
                {
                    "title": "准备周报和复盘材料",
                    "priority": "中优先级",
                    "priority_class": "medium",
                    "meta": "明天 10:00",
                    "tag": "周报",
                    "completed": False,
                },
                {
                    "title": "复盘本周任务完成情况",
                    "priority": "低优先级",
                    "priority_class": "low",
                    "meta": "周五 17:30",
                    "tag": "复盘",
                    "completed": False,
                },
            ],
        },
        {
            "key": "someday",
            "eyebrow": "NO DATE",
            "title": "还没有安排日期",
            "subtitle": "先收集，等准备好再安排时间",
            "count": 2,
            "accent": "violet",
            "tasks": [
                {
                    "title": "阅读 Flask 官方文档",
                    "priority": "低优先级",
                    "priority_class": "low",
                    "meta": "暂无截止日期",
                    "tag": "阅读",
                    "completed": False,
                },
                {
                    "title": "整理灵感收集箱",
                    "priority": "低优先级",
                    "priority_class": "low",
                    "meta": "暂无截止日期",
                    "tag": "收集",
                    "completed": False,
                },
            ],
        },
    ]


@today_bp.route("")
@today_bp.route("/")
def today_page():
    """渲染 Today 工作台的 UI 预览。"""
    current_date = date.today()
    return render_template(
        "today.html",
        current_date=current_date.strftime("%Y年%m月%d日"),
        current_weekday=_WEEKDAYS[current_date.weekday()],
        sections=_demo_sections(),
    )
