# Git 初始化和推送指南

## 📋 前提条件

### 1. 安装 Git

如果尚未安装 Git，请先安装：

**Windows 用户**:
1. 访问 https://git-scm.com/download/win
2. 下载并安装 Git for Windows
3. 安装完成后重启终端

**验证安装**:
```bash
git --version
```

---

## 🚀 快速开始

### 步骤 1: 初始化 Git 仓库

在项目根目录执行：
```bash
cd task-manager
git init
```

### 步骤 2: 添加所有文件

```bash
git add .
```

### 步骤 3: 提交代码

```bash
git commit -m "Initial commit: 个人任务管理系统 v1.0

功能包括:
- 命令行任务管理 (CRUD)
- 任务搜索和过滤
- 统计报表和周报
- 任务提醒功能
- Web 界面 (Flask)
- 完整的单元测试
- 多页面统计仪表板
- Chart.js 数据可视化"
```

### 步骤 4: 关联远程仓库

```bash
git remote add origin https://github.com/liuGuanYi-hub/task-manager.git
```

### 步骤 5: 推送到 GitHub

```bash
# 如果是第一次推送
git branch -M main
git push -u origin main

# 后续推送
git push origin main
```

---

## 🔧 常见问题解决

### 问题 1: Git 未找到

**错误**: `git: 无法将"git"项识别为 cmdlet...`

**解决**:
1. 安装 Git: https://git-scm.com/download/win
2. 安装时选择"添加到 PATH"
3. 重启终端

### 问题 2: 认证失败

**错误**: `Authentication failed`

**解决方式 1 - 使用 Personal Access Token**:
1. 访问 https://github.com/settings/tokens
2. 创建新 token (勾选 repo 权限)
3. 使用 token 代替密码：
   ```bash
   git push https://<your-username>:<your-token>@github.com/liuGuanYi-hub/task-manager.git
   ```

**解决方式 2 - 使用 SSH**:
```bash
# 生成 SSH 密钥
ssh-keygen -t ed25519 -C "your_email@example.com"

# 添加公钥到 GitHub
# 访问 https://github.com/settings/keys

# 更改远程仓库为 SSH
git remote set-url origin git@github.com:liuGuanYi-hub/task-manager.git

# 推送
git push -u origin main
```

### 问题 3: 远程仓库已存在

**错误**: `remote origin already exists`

**解决**:
```bash
# 删除现有远程
git remote remove origin

# 重新添加
git remote add origin https://github.com/liuGuanYi-hub/task-manager.git
```

### 问题 4: 推送被拒绝

**错误**: `rejected master -> main (fetch first)`

**解决**:
```bash
# 拉取远程变更
git pull origin main --allow-unrelated-histories

# 解决冲突（如果有）

# 再次推送
git push -u origin main
```

---

## 📝 一键执行脚本

### Windows PowerShell

创建 `deploy.ps1` 脚本：

```powershell
# deploy.ps1
Write-Host "🚀 开始部署到 GitHub..." -ForegroundColor Green

# 初始化 Git
Write-Host "`n📦 初始化 Git 仓库..." -ForegroundColor Yellow
git init

# 添加文件
Write-Host "`n📝 添加所有文件..." -ForegroundColor Yellow
git add .

# 提交
Write-Host "`n💾 提交代码..." -ForegroundColor Yellow
git commit -m "Initial commit: 个人任务管理系统"

# 设置分支
Write-Host "`n🔀 设置主分支..." -ForegroundColor Yellow
git branch -M main

# 关联远程
Write-Host "`n🔗 关联远程仓库..." -ForegroundColor Yellow
git remote add origin https://github.com/liuGuanYi-hub/task-manager.git

# 推送
Write-Host "`n📤 推送到 GitHub..." -ForegroundColor Yellow
git push -u origin main

Write-Host "`n✅ 部署完成！" -ForegroundColor Green
Write-Host "🌐 访问：https://github.com/liuGuanYi-hub/task-manager" -ForegroundColor Cyan
```

**执行脚本**:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\deploy.ps1
```

---

## 🎯 完整命令清单

```bash
# 1. 进入项目目录
cd task-manager

# 2. 初始化 Git
git init

# 3. 添加所有文件
git add .

# 4. 提交
git commit -m "Initial commit"

# 5. 设置主分支
git branch -M main

# 6. 关联远程仓库
git remote add origin https://github.com/liuGuanYi-hub/task-manager.git

# 7. 推送
git push -u origin main
```

---

## 📊 项目文件清单

推送前确认包含以下文件：

```
task-manager/
├── .gitignore              ✅ 已创建
├── LICENSE                 ✅ 已创建
├── README.md               ✅ 已存在
├── requirements.txt        ✅ 已存在
├── main.py                 ✅ 已存在
├── web_app.py              ✅ 已存在
├── models/
│   ├── __init__.py        ✅ 已存在
│   └── task.py            ✅ 已存在
├── storage/
│   ├── __init__.py        ✅ 已存在
│   └── json_storage.py    ✅ 已存在
├── commands/
│   ├── __init__.py        ✅ 已存在
│   ├── create.py          ✅ 已存在
│   ├── list_tasks.py      ✅ 已存在
│   ├── update.py          ✅ 已存在
│   ├── delete.py          ✅ 已存在
│   ├── search.py          ✅ 已存在
│   ├── stats.py           ✅ 已存在
│   └── remind.py          ✅ 已存在
├── utils/
│   ├── __init__.py        ✅ 已存在
│   └── helpers.py         ✅ 已存在
├── routes/
│   ├── __init__.py        ✅ 已存在
│   ├── stats_routes.py    ✅ 已存在
│   ├── tags_routes.py     ✅ 已存在
│   └── weekly_routes.py   ✅ 已存在
├── tests/
│   ├── __init__.py        ✅ 已存在
│   ├── test_task.py       ✅ 已存在
│   └── test_storage.py    ✅ 已存在
└── dev-plans/             ✅ 文件夹
    ├── README.md
    ├── 个人任务管理系统.md
    ├── Web 界面扩展计划.md
    └── Web 界面扩展总结.md
```

---

## 🎨 提交信息规范

使用 Conventional Commits 规范：

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**常用类型**:
- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具

**示例**:
```bash
git commit -m "feat(web): 添加统计仪表板页面

- 实现 Chart.js 数据可视化
- 添加 3 种图表类型
- 优化响应式布局

Closes #12"
```

---

## 📈 后续维护

### 日常开发流程

```bash
# 1. 开发新功能
# ... 编写代码 ...

# 2. 查看变更
git status
git diff

# 3. 添加文件
git add <filename>

# 4. 提交
git commit -m "feat: 新功能描述"

# 5. 推送
git push origin main
```

### 查看历史记录

```bash
# 查看提交历史
git log

# 简洁模式
git log --oneline

# 图形化显示
git log --graph --oneline --all
```

### 回退版本

```bash
# 回退到上一个版本
git reset --hard HEAD~1

# 回退到指定版本
git reset --hard <commit-hash>
```

---

## 🔗 相关链接

- [Git 官方文档](https://git-scm.com/doc)
- [GitHub 帮助](https://docs.github.com/)
- [Git 教程 - 廖雪峰](https://www.liaoxuefeng.com/wiki/896043488029600)
- [Conventional Commits](https://www.conventionalcommits.org/)

---

## ✅ 检查清单

推送前确认：

- [ ] Git 已安装
- [ ] GitHub 账号已登录
- [ ] 远程仓库已创建
- [ ] .gitignore 已配置
- [ ] LICENSE 已添加
- [ ] README.md 已更新
- [ ] 所有代码已测试
- [ ] 敏感信息已排除

---

准备好后，执行上述命令即可完成 Git 初始化和推送！🚀
