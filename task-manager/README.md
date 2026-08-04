# 个人任务管理系统

一个功能完整的命令行任务管理工具，使用 Python 开发，支持 Web 界面。

## 特性

✅ 任务 CRUD 操作  
✅ 任务搜索和过滤  
✅ 统计报表和周报  
✅ 任务提醒功能  
✅ 每日摘要  
✅ Web 界面  
✅ 显式项目和项目级任务隔离
✅ WeKan 式三列任务看板
✅ 完整的单元测试  

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
# 删除任务（会提示确认）
python main.py delete-task 1

# 直接删除
python main.py delete-task 1 -y
```

### 3. Web 界面

启动 Web 服务器：
```bash
python web_app.py
```

然后在浏览器访问：http://localhost:5000

## 项目结构

```
task-manager/
├── main.py              # 主程序入口
├── web_app.py           # Web 应用
├── models/              # 数据模型
│   ├── task.py
│   └── project.py
├── storage/             # 数据存储
│   └── json_storage.py
├── commands/            # 命令处理
│   ├── create.py
│   ├── projects.py
│   ├── list_tasks.py
│   ├── update.py
│   ├── delete.py
│   ├── search.py
│   ├── stats.py
│   └── remind.py
├── utils/               # 工具函数
│   └── helpers.py
├── tests/               # 测试文件
│   ├── test_task.py
│   ├── test_storage.py
│   ├── test_phase_0_1.py
│   ├── test_phase_2.py
│   └── test_phase_3.py
├── requirements.txt     # 依赖包
└── README.md           # 说明文档
```

## 运行测试

```bash
python -m pytest tests/ -v
```

## 开发计划

详见：`../dev-plans/个人任务管理系统.md`
