# Task Manager

Task Manager 是一个个人任务管理系统，提供命令行和 Flask Web 两种使用方式，适合记录任务、安排截止日期、推进看板、搜索过滤、统计复盘和安全备份。

## 功能概览

- 任务 CRUD、Today 工作台和任务详情抽屉
- WeKan 式三列看板，状态拖拽后持久化
- 项目级任务隔离和可保存组合筛选视图
- 全局搜索、提醒中心、日历和归档恢复
- JSON/SQLite 双存储与 REST API v1
- API Bearer Token、分页、健康检查和能力发现
- 浅色/深色/系统主题、移动端导航和可访问性基础
- GitHub Actions、敏感信息扫描和 100+ 回归测试

## 技术栈

- Python
- Flask
- JSON 本地存储
- pytest

## 项目结构

```text
task-Manager/
├── task-manager/   # 主应用
└── dev-plans/      # 开发计划文档
```

## 本地启动

```bash
cd task-manager
pip install -r requirements.txt
```

建议在项目虚拟环境中安装依赖，不要把项目依赖安装到系统 Python。

### 命令行

```bash
python main.py list-tasks
python main.py create-task "学习 Python"
```

### Web 界面

```bash
python web_app.py
```

访问：

```text
http://localhost:5000
```

### 主题模式

打开 `/settings/` 可以选择跟随系统、浅色或深色模式，并选择默认、玫瑰、海洋或薄荷强调色。设置会保存在当前浏览器的 `localStorage` 中；页面右上角的“主题模式”按钮可快速循环切换三种模式。跟随系统模式会响应操作系统的浅色/深色偏好变化。

### 发布前检查

在仓库根目录执行：

```bash
python task-manager/scripts/security_scan.py --root .
cd task-manager
python -m pytest tests/ -q
python -m compileall -q models storage commands routes utils scripts web_app.py main.py
git diff --check
```

GitHub Actions 会在 push 和 pull request 时自动执行同一组核心检查。当前默认分支为 `master`，提交信息使用中文，发布时只暂存本轮明确修改的文件。

## 测试

```bash
python -m pytest tests/ -v
```

## 仓库

```text
https://github.com/liuGuanYi-hub/task-manager
```

## 进一步文档

- [应用说明与 API 概览](task-manager/README.md)
- [REST API v1 契约](task-manager/docs/API.md)
- [开发计划](dev-plans/个人任务管理系统.md)
- [部署与发布检查](task-manager/DEPLOY.md)

## 动态系统架构图

![Task Manager 动态系统架构图](docs/architecture/dynamic-archify-architecture.gif)

- [打开交互式动态架构图](docs/architecture/dynamic-archify-architecture.html)
- [查看架构源数据](docs/architecture/dynamic-archify-architecture.json)
