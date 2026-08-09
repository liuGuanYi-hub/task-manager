# 🚀 当前部署与发布指南

> 当前仓库使用 `master` 分支。本文优先介绍可审计的手动发布流程；旧版一键脚本保留在仓库中，但不建议用于当前工作区，因为它会执行宽范围 `git add .`、尝试切换分支并沿用早期发布假设。

## 当前推荐流程

从仓库根目录执行：

```powershell
# 1. 查看工作区，确认没有把无关删除或敏感文件纳入本轮
git status --short

# 2. 发布前验证
python task-manager/scripts/security_scan.py --root .
Set-Location task-manager
python -m pytest tests/ -q
python -m compileall -q models storage commands routes utils scripts web_app.py main.py
git diff --check
Set-Location ..

# 3. 只暂存本轮明确修改的路径
git add <本轮明确修改的文件>
git diff --cached --check

# 4. 使用中文提交信息并推送当前分支
git commit -m "完善：说明本轮发布内容"
git push origin master
```

GitHub Actions 会在 push 和 pull request 时重复执行核心质量门禁。推送完成后，在仓库 Actions 页面确认工作流通过，再进行正式演示或部署。

## 配置 API Token

不要把 token 放进 Git remote URL、脚本、日志或 Markdown。部署时通过系统服务、CI secret 或部署平台环境变量注入：

```powershell
$env:TASK_MANAGER_API_TOKEN = "YOUR_API_TOKEN"
python task-manager/web_app.py
```

配置 token 后，只有 `/api/v1` 和 `/api/v1/health` 公开；其余 API 请求使用 `Authorization: Bearer YOUR_API_TOKEN`。

## 旧版自动部署脚本（不建议用于当前工作区）

### Windows 用户

1. **打开 PowerShell**
   - 在项目目录右键，选择"在终端中打开"
   - 或按 `Win+X` 选择 Windows PowerShell

2. **执行部署脚本**
   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\deploy.ps1
   ```

3. **按提示操作**
   - 脚本会自动完成 Git 初始化
   - 添加所有文件
   - 提交代码
   - 关联远程仓库
   - 推送到 GitHub

4. **输入认证信息**
   - GitHub 用户名
   - Personal Access Token（推荐）或密码

---

## 方式二：手动命令

### 步骤清单

```bash
# 1. 进入项目目录
cd task-manager

# 2. 初始化 Git
git init

# 3. 添加所有文件
git add <本轮明确修改的文件>

# 4. 提交
git commit -m "Initial commit: 个人任务管理系统 v1.0"

# 5. 设置分支
git branch -M master

# 6. 关联远程仓库
git remote add origin https://github.com/liuGuanYi-hub/task-manager.git

# 7. 推送
git push -u origin master
```

---

## 🔑 GitHub 认证设置

### 使用 Personal Access Token（推荐）

1. **创建 Token**
   - 访问：https://github.com/settings/tokens
   - 点击 "Generate new token (classic)"
   - 勾选权限：`repo` (Full control of private repositories)
   - 生成并复制 Token

2. **使用 Token 推送**
   ```bash
   git push origin master
   ```

   推荐使用 Git Credential Manager 或 SSH 保存认证，不要把 token 拼接进 URL。

### 使用 SSH 密钥

1. **生成 SSH 密钥**
   ```bash
   ssh-keygen -t ed25519 -C "your_email@example.com"
   ```

2. **添加公钥到 GitHub**
   - 访问：https://github.com/settings/keys
   - 点击 "New SSH key"
   - 粘贴 `~/.ssh/id_ed25519.pub` 内容

3. **切换为 SSH 地址**
   ```bash
   git remote set-url origin git@github.com:liuGuanYi-hub/task-manager.git
   ```

---

## ✅ 验证部署

### 1. 检查远程仓库

访问：https://github.com/liuGuanYi-hub/task-manager

应该看到：
- ✅ 所有项目文件
- ✅ README.md 内容
- ✅ 提交历史

### 2. 查看提交记录

```bash
git log --oneline
```

### 3. 检查远程仓库状态

```bash
git remote -v
git status
```

---

## 🐛 常见问题

### 问题 1: 权限被拒绝

```
fatal: Could not read from remote repository.
```

**解决**: 
- 确认 Token 有效
- 检查 Token 权限设置
- 重新生成 Token

### 问题 2: 远程仓库不存在

```
remote: Repository not found.
```

**解决**:
1. 在 GitHub 创建新仓库
2. 仓库名：`task-manager`
3. 不要初始化（README, .gitignore, license）

### 问题 3: 推送大文件

```
fatal: The remote end hung up unexpectedly
```

**解决**:
```bash
# 安装 Git LFS
git lfs install

# 跟踪大文件
git lfs track "*.psd"
git lfs track "*.zip"

# 重新添加
git add .gitattributes
git commit -m "Configure Git LFS"
```

---

## 📊 部署检查清单

部署前确认：

- [ ] Git 已安装 (`git --version`)
- [ ] GitHub 账号已登录
- [ ] 远程仓库已创建（空仓库）
- [ ] Personal Access Token 已生成
- [ ] .gitignore 已配置
- [ ] 敏感信息已删除
- [ ] 代码已测试

---

## 🎯 部署后操作

### 1. 更新 GitHub 仓库描述

- 访问仓库主页
- 点击 "About" 设置
- 添加描述、网站、话题

### 2. 添加 Topics

推荐 topics:
```
python flask task-management web-app cli chartjs
```

### 3. 保护主分支

- Settings → Branches
- Add branch protection rule
- Branch name: `main`
- 勾选保护选项

### 4. 启用 GitHub Pages（可选）

- Settings → Pages
- Source: Deploy from branch
- Branch: main
- Folder: / (root)

---

## 📈 后续开发流程

### 日常开发

```bash
# 1. 开发新功能
# ... 编写代码 ...

# 2. 查看变更
git status
git diff

# 3. 添加并提交
git add .
git commit -m "feat: 新功能描述"

# 4. 推送
git push origin main
```

### 版本发布

```bash
# 1. 打标签
git tag -a v1.0.0 -m "Release version 1.0.0"

# 2. 推送标签
git push origin v1.0.0

# 3. 在 GitHub 创建 Release
# https://github.com/liuGuanYi-hub/task-manager/releases
```

---

## 🔗 相关资源

- [Git 官方文档](https://git-scm.com/doc)
- [GitHub 帮助](https://docs.github.com/)
- [Git 教程](https://www.liaoxuefeng.com/wiki/896043488029600)
- [Personal Access Token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)

---

## 📞 需要帮助？

如果遇到问题：

1. 查看 `GIT_SETUP.md` 详细指南
2. 运行 `.\deploy.ps1` 自动诊断
3. 检查错误信息并搜索解决方案

---

**准备好部署了吗？** 运行 `.\deploy.ps1` 开始！ 🚀
