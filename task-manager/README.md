# 个人任务管理系统

一个功能完整的命令行任务管理工具，使用 Python 开发，支持 Web 界面。

## 特性

当前版本重点能力：Today 工作台、统一任务详情抽屉、Inbox 收集箱与任务分流、Agenda 七天日程时间线（筛选 + 拖拽 / 触控 / 键盘改期）、统一任务快速操作与撤销回滚、统一视图 Shell、WeKan 式看板状态持久化、保存视图、提醒中心、归档恢复、JSON/SQLite 双存储、REST API v1 认证分页、深色主题、移动端导航、可访问性基础和 GitHub Actions 质量门禁。

✅ 任务 CRUD 操作  
✅ 任务搜索和过滤  
✅ 统计报表和周报  
✅ 任务提醒功能  
✅ 每日摘要  
✅ Web 界面  
✅ 显式项目和项目级任务隔离
✅ WeKan 式三列任务看板
✅ 可保存的组合筛选视图
✅ 归档、恢复和安全备份导入
✅ JSON/SQLite 存储后端可切换
✅ REST API（/api/v1）
✅ Inbox 收集箱（先收集再规划，三种分流方式）
✅ Agenda 七天日程时间线（三层筛选 + 鼠标 / 触控 / 键盘改期）
✅ 统一任务操作与撤销回滚（乐观锁防冲突）
✅ 统一视图 Shell（分组导航 + 全局搜索 + 移动端底部导航）
✅ 完整的单元测试（45 个测试文件）  

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 命令行使用

#### 创建任务
```bash
# 创建简单任务
python main.py create-task "学习 Python"

# 创建带描述和优先级的任务
python main.py create-task "完成项目报告" -d "周五前提交" -p 高

# 创建带截止时间的任务
python main.py create-task "提交作业" --due-date "2026-08-08 18:00"

# 添加标签
python main.py create-task "阅读技术文章" -t 学习 -t 技术

# 将任务归属到项目
python main.py create-task "完成项目报告" --project-id 1
```

#### 项目管理
```bash
# 创建项目
python main.py create-project "个人学习" -d "课程和技术学习任务"

# 查看项目
python main.py list-projects

# 更新项目
python main.py update-project 1 --name "长期学习"

# 只查看某个项目的任务
python main.py list-tasks --project-id 1

# 只查看未归属项目的任务
python main.py list-tasks --no-project
```

项目与标签是两个独立概念：`project_id` 用于项目级隔离，标签继续用于跨项目分类。历史 JSON 中没有 `project_id` 的任务会保留为未归属项目，不会根据标签自动迁移。

#### 看板
浏览器访问 `http://localhost:5000/board`，即可按“待办 / 进行中 / 已完成”查看任务。看板支持按项目筛选，并可在任务卡片内直接选择新状态后提交；状态变化会同步保存到 JSON，任务列表和项目详情会读取同一结果。

#### Inbox 收集箱
浏览器访问 `http://localhost:5000/inbox`。Inbox 遵循“先收集，再规划”的思路，只显示未归档且没有截止日期的任务。每条任务提供三种分流方式：

- **安排到今天**：把 `due_date` 设为今天的 00:00
- **安排到指定日期**：输入日期后设置 `due_date`
- **归入项目**：设置 `project_id`，不设日期（任务仍留在 Inbox）

分流后任务自动移出 Inbox，进入对应的工作台 / 项目视图。Inbox 内还支持直接快速完成 / 恢复（toggle）和快速归档。

#### Agenda 日程时间线
浏览器访问 `http://localhost:5000/agenda`。Agenda 把截止日期变成一条可执行的七天时间线，并提供三层筛选：

- **日期筛选**：七天时间线 / 选中日期 / 逾期任务 / 未安排任务
- **密度筛选**：全部 / 有任务的日子 / 高密度（3 项以上）/ 空白日
- **时间段筛选**：深夜 00:00–06:00 / 上午 06:00–12:00 / 下午 12:00–18:00 / 晚上 18:00–24:00

改期支持三种交互方式，均通过 `/calendar/task/<id>/reschedule` 持久化（保留原截止时间，只改日期）：

- **鼠标拖拽**：拖拽任务卡片到目标日期的 dropzone
- **触控拖拽**：长按 420ms 激活拖拽模式，松手落位
- **键盘改期**：聚焦任务后按 `R` 进入改期模式，左右箭头移动日期，`Enter` 保存、`Esc` 取消

改期采用乐观更新：先移动 DOM，保存成功后刷新；失败自动回滚。右侧“未安排任务”侧栏提供“今天 / 明天 / 下周一”快捷安排按钮。

#### 保存视图
浏览器访问 `http://localhost:5000/views`，可以组合项目、状态、优先级、标签、截止日期和排序条件。页面内置“高优先级未完成”和“本周到期”预设，也可以给当前筛选命名保存，之后从“保存视图”导航中读取或删除。

#### 查看任务
```bash
# 查看所有任务
python main.py list-tasks

# 按状态筛选
python main.py list-tasks -s 待办

# 按优先级筛选
python main.py list-tasks -p 高

# 按标签筛选
python main.py list-tasks -t 学习
```

#### 搜索任务
```bash
# 搜索关键词
python main.py search-tasks Python

# 只在标题中搜索
python main.py search-tasks 报告 --title
```

#### 统计报表
```bash
# 查看统计
python main.py stats

# 详细统计
python main.py stats --detail

# 周报
python main.py weekly-report --days 7
```

#### 任务提醒
```bash
# 查看提醒
python main.py remind

# 每日摘要
python main.py daily-summary
```

#### 更新任务
```bash
# 更新状态
python main.py update-task 1 -s 进行中

# 更新优先级
python main.py update-task 1 -p 高

# 更新截止时间
python main.py update-task 1 --due-date "2026-08-08 18:00"

# 清除截止时间
python main.py update-task 1 --due-date ""
```

#### 删除任务
```bash
# 归档任务（会提示确认，可从 Web 的“归档”页面恢复）
python main.py delete-task 1

# 归档任务并跳过确认
python main.py delete-task 1 -y

# 明确执行永久删除（不可恢复）
python main.py delete-task 1 -y --permanent
```

### 3. Web 界面

启动 Web 服务器：
```bash
python web_app.py
```

然后在浏览器访问：http://localhost:5000

归档任务：`http://localhost:5000/archive`；保存视图：`http://localhost:5000/views`；备份和导入：`http://localhost:5000/settings`。

#### 统一任务操作与撤销

所有页面共享同一个任务详情抽屉（`_task_detail_drawer.html`），其中的快速操作统一走 `POST /task/<id>/action` 端点：

| 动作 | 说明 |
|---|---|
| `complete` | 标记为已完成 |
| `reopen` / `toggle` | 恢复为待办 |
| `archive` | 归档任务 |
| `delay` | 延后到明天（默认 09:00）或指定日期 |
| `undo` | 撤销上一步操作 |

撤销采用快照机制：每次操作前保存任务完整快照，撤销时校验当前状态与预期一致（不一致返回 `409 undo_conflict`，防止并发覆盖），成功则恢复全部业务字段；存储更新失败时内存状态同步回滚。前端操作成功后显示 5 秒倒计时撤销面板，点击“撤销”即回滚。

### 4. SQLite 与 REST API

默认仍使用 `tasks.json`。需要切换 SQLite 时，通过环境变量选择后端：

```powershell
$env:TASK_MANAGER_STORAGE = "sqlite"
$env:TASK_MANAGER_SQLITE_PATH = "tasks.db"
python web_app.py
```

CLI 和 Web 使用同一个存储工厂，未设置变量时不会改变原有 JSON 行为。可以先把已有 JSON 数据迁移到新的 SQLite 文件：

```bash
python main.py migrate-sqlite tasks.json --sqlite-path tasks.db
```

迁移默认使用 `replace` 策略，重复执行同一个 JSON 文件不会重复已有 ID；`--conflict` 也支持 `remap` 和 `skip`。不要把 SQLite 目标路径指向原有 JSON 文件。

REST API 基础路径为 `/api/v1`：

访问 `/api/v1` 可以查看当前 API 版本、认证要求、分页限制和端点发现信息；完整请求体、筛选参数和错误响应请参阅 [`docs/API.md`](docs/API.md)。

| 方法 | 路径 | 用途 |
|---|---|---|
| GET | `/health` | 查看 API 和当前存储后端状态 |
| GET/POST | `/tasks` | 查询或创建任务 |
| GET/PATCH/DELETE | `/tasks/<id>` | 查询、更新或归档任务 |
| GET/POST | `/projects` | 查询或创建项目 |
| GET | `/projects/<id>` | 查询项目及其任务 |

API 的 `DELETE /tasks/<id>` 与 Web/CLI 一致，执行归档而不是永久删除；`include_archived=1` 可在查询时包含归档任务。

#### API 认证

本地未配置 token 时保持开发兼容模式。部署或对外提供 API 时设置环境变量：

```powershell
$env:TASK_MANAGER_API_TOKEN = "在安全配置中设置的值"
python web_app.py
```

除 `/api/v1` 和 `/api/v1/health` 外，请求必须携带：

```text
Authorization: Bearer <已配置的 token>
```

服务不会把 token 写入日志或响应。token 建议通过系统服务管理器、部署平台密钥或其他安全配置注入，不要提交到 Git。

#### API 分页

任务集合、项目集合和项目详情中的任务支持 `page` 与 `page_size` 参数，默认每页 20 条，最大 100 条：

```text
GET /api/v1/tasks?page=2&page_size=20&sort_by=id
GET /api/v1/projects?page=1&page_size=10
```

响应的 `meta` 包含 `page`、`page_size`、`pages`、`total`、`count` 和 `returned`，其中 `returned` 是当前页实际返回数量。

使用 SQLite 后，任务集合、项目集合和项目详情任务会直接执行数据库 `COUNT(*)`、过滤、排序和 `LIMIT/OFFSET`；JSON 后端继续使用原有内存兼容路径。旧版 SQLite 文件中的 `tags_json` 会在启动时回填到标签索引表，不影响按标签查询。

### 5. 发布前检查

从仓库根目录运行：

```bash
python task-manager/scripts/security_scan.py --root .
cd task-manager
python -m pytest tests/ -q
python -m compileall -q models storage commands routes utils scripts web_app.py main.py
git diff --check
```

Windows 下还可以运行隔离发布 smoke；脚本会在 `output/release-smoke/` 创建独立 SQLite 和浏览器证据，不使用默认任务文件：

```powershell
python task-manager/scripts/release_smoke.py
```

不要把真实 token、`.env`、任务 JSON 或 SQLite 文件提交到 Git。GitHub Actions 会在 push 和 pull request 时执行测试、编译、JavaScript 语法、空白和敏感信息扫描。

## 项目结构

```
task-manager/
├── main.py              # 主程序入口（CLI）
├── web_app.py           # Web 应用（注册 16 个 Blueprint）
├── models/              # 数据模型
│   ├── task.py
│   ├── project.py
│   └── saved_view.py
├── storage/             # 数据存储
│   ├── interface.py
│   ├── factory.py
│   ├── json_storage.py
│   └── sqlite_storage.py
├── commands/            # 命令处理
│   ├── create.py
│   ├── projects.py
│   ├── list_tasks.py
│   ├── update.py
│   ├── delete.py
│   ├── search.py
│   ├── stats.py
│   ├── remind.py
│   └── storage.py
├── routes/              # Flask 页面和 API 路由（16 个 Blueprint）
│   ├── today_routes.py      # Today 工作台
│   ├── inbox_routes.py      # Inbox 收集箱与任务分流
│   ├── agenda_routes.py     # Agenda 七天日程时间线
│   ├── board_routes.py      # WeKan 看板
│   ├── calendar_routes.py   # 日历 + 拖拽改期
│   ├── views_routes.py      # 保存视图
│   ├── projects_routes.py   # 项目
│   ├── search_routes.py     # 全局搜索
│   ├── reminder_routes.py   # 提醒中心
│   ├── archive_routes.py    # 归档恢复
│   ├── stats_routes.py      # 统计面板
│   ├── tags_routes.py       # 标签管理
│   ├── weekly_routes.py     # 周报
│   ├── settings_routes.py   # 设置
│   ├── task_actions.py      # 统一任务操作 + 撤销
│   └── api_routes.py        # REST API v1
├── templates/           # Jinja2 模板（22 个，含统一视图 Shell base.html）
├── static/              # 前端资源（agenda.js / today.js / app.css 等）
├── utils/               # 工具函数和安全脱敏
│   ├── helpers.py
│   └── security.py
├── scripts/             # 发布前维护脚本
│   ├── security_scan.py
│   └── release_smoke.py
├── docs/                # 接口契约
│   ├── API.md
│   └── SCHEMA_MIGRATION_PLAN.md
├── tests/               # 测试文件（45 个，0.1 ~ 16.6 各阶段）
│   ├── test_task.py
│   ├── test_storage.py
│   ├── test_phase_0_1.py ~ test_phase_16_6.py
│   └── ...
├── requirements.txt     # 依赖包
└── README.md           # 说明文档
```

## 运行测试

```bash
python -m pytest tests/ -v
```

## 开发计划

详见：`../dev-plans/个人任务管理系统.md`
