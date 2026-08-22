# Task Manager — 个人任务管理系统

> **CLI + Web 双形态 · Inbox 收集分流 · Agenda 七天日程 · 看板拖拽 · 撤销回滚 · 100+ 回归测试**

Task Manager 是一个面向个人的任务管理系统，同时提供命令行与 Flask Web 两种使用方式，覆盖收集、排期、推进、复盘的全流程，数据存本机、可安全备份。

---

## ✨ 核心特性

- 📥 **Inbox 收集箱与任务分流**：未排期任务统一收集，一键安排到今天、指定日期或归入项目。
- 📅 **Agenda 七天日程时间线**：日期 / 密度 / 时间段三层筛选，支持鼠标拖拽、触控长按、键盘三种改期方式。
- ⚡ **统一任务快速操作与撤销回滚**：完成 / 恢复 / 归档 / 延后 / 撤销一气呵成，乐观锁防并发冲突。
- 🧩 **统一视图 Shell**：分组导航、工作区工具栏、全局搜索与移动端底部导航。
- 🗂️ **WeKan 式三列看板**：状态拖拽后持久化。
- 🔍 **项目隔离与组合筛选视图**：项目级任务隔离，可保存常用筛选组合。
- 🔔 **提醒中心、日历与归档恢复**：全局搜索、月视图拖拽改期、归档任务可找回。
- 🗄️ **JSON / SQLite 双存储与 REST API v1**：Bearer Token、分页、健康检查和能力发现。
- 🎨 **浅色 / 深色 / 系统主题**：四种强调色，跟随系统深浅色偏好，设置存于浏览器 `localStorage`。
- ✅ **质量保障**：GitHub Actions、敏感信息扫描、45 个测试文件（100+ 回归测试）、16 个路由 Blueprint。

---

## 🚀 快速开始

### 1. 安装依赖

```bash
cd task-manager
pip install -r requirements.txt
```

建议在项目虚拟环境中安装依赖，不要把项目依赖安装到系统 Python。

### 2. 命令行方式

```bash
python main.py list-tasks
python main.py create-task "学习 Python"
```

### 3. Web 界面

```bash
python web_app.py
```

访问 `http://localhost:5000`，主要页面入口：

- `/today` — Today 工作台（今天 / 逾期 / 接下来 / 无日期四段式分组）
- `/inbox` — Inbox 收集箱（只显示未排期任务，可分流到今天、指定日期或项目）
- `/agenda` — Agenda 七天日程时间线（筛选 + 拖拽 / 触控 / 键盘改期）
- `/board` — WeKan 式三列看板
- `/calendar` — 日历月视图与拖拽改期
- `/views` — 可保存组合筛选视图
- `/reminders` — 提醒中心
- `/archive` — 归档与恢复

主题与强调色在 `/settings/` 中配置；页面右上角「主题模式」按钮可快速循环切换三种模式。

---

## 📂 项目结构

```text
task-Manager/
├── task-manager/        # 主应用（Flask Web + CLI）
│   ├── models/          # 任务等领域模型
│   ├── storage/         # JSON / SQLite 双存储层
│   ├── commands/        # CLI 命令
│   ├── routes/          # 16 个路由 Blueprint
│   ├── templates/       # 页面模板
│   ├── static/          # 前端脚本与样式
│   ├── tests/           # 45 个测试文件
│   ├── scripts/         # 安全扫描等脚本
│   └── docs/API.md      # REST API v1 契约
├── dev-plans/           # 开发计划文档
└── docs/architecture/   # 动态系统架构图
```

---

## 🛠️ 技术栈

- Python + Flask（Web 服务与 CLI）
- JSON 本地存储（可选 SQLite）
- pytest 回归测试

---

## 🧪 测试与发布检查

```bash
# 测试
python -m pytest tests/ -v

# 发布前检查（仓库根目录执行）
python task-manager/scripts/security_scan.py --root .
cd task-manager
python -m pytest tests/ -q
python -m compileall -q models storage commands routes utils scripts web_app.py main.py
git diff --check
```

GitHub Actions 会在 push 和 pull request 时自动执行同一组核心检查。当前默认分支为 `master`，提交信息使用中文，发布时只暂存本轮明确修改的文件。测试覆盖任务模型、存储层和 0.1 ~ 16.6 各阶段功能（含 Inbox 分流、统一操作撤销回滚、Agenda 筛选与改期契约等）。

---

## 🏗️ 动态系统架构图

![Task Manager 动态系统架构图](docs/architecture/dynamic-archify-architecture.gif)

- [打开交互式动态架构图](docs/architecture/dynamic-archify-architecture.html)
- [查看架构源数据](docs/architecture/dynamic-archify-architecture.json)

---

## 📚 进一步文档

- [应用说明与 API 概览](task-manager/README.md)
- [REST API v1 契约](task-manager/docs/API.md)
- [开发计划](dev-plans/个人任务管理系统.md)
- [部署与发布检查](task-manager/DEPLOY.md)

---

## 📄 仓库与许可证

仓库地址：https://github.com/liuGuanYi-hub/task-manager
