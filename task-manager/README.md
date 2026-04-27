# 个人任务管理系统

一个功能完整的命令行任务管理工具，使用 Python 开发，支持 Web 界面。

## 特性

✅ 任务 CRUD 操作  
✅ 任务搜索和过滤  
✅ 统计报表和周报  
✅ 任务提醒功能  
✅ 每日摘要  
✅ Web 界面  
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

# 添加标签
python main.py create-task "阅读技术文章" -t 学习 -t 技术
```

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
│   └── task.py
├── storage/             # 数据存储
│   └── json_storage.py
├── commands/            # 命令处理
│   ├── create.py
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
│   └── test_storage.py
├── requirements.txt     # 依赖包
└── README.md           # 说明文档
```

## 运行测试

```bash
python -m pytest tests/ -v
```

## 开发计划

详见：`../dev-plans/个人任务管理系统.md`
