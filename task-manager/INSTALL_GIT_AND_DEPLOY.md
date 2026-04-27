# 🚀 一键安装 Git 并部署

## 检测到 Git 未安装

您的系统当前未安装 Git，需要先安装 Git 才能推送到 GitHub。

---

## 📦 方案一：手动安装 Git（推荐）

### 步骤 1: 下载 Git

访问：https://git-scm.com/download/win

或点击下载（Windows）：
- 64 位：https://github.com/git-for-windows/git/releases/download/v2.45.1.windows.1/Git-2.45.1-64-bit.exe
- 32 位：https://github.com/git-for-windows/git/releases/download/v2.45.1.windows.1/Git-2.45.1-32-bit.exe

### 步骤 2: 安装 Git

1. 双击下载的安装文件
2. 一直点击"Next"
3. **重要**: 选择"Git from the command line and also from 3rd-party software"
4. 完成安装

### 步骤 3: 验证安装

打开新的 PowerShell 窗口，运行：
```powershell
git --version
```

应该显示：`git version 2.x.x.windows.x`

### 步骤 4: 运行部署脚本

```powershell
cd C:\Users\Administrator\Desktop\zzd\task-manager
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\deploy.ps1
```

---

## 🚀 方案二：使用 winget 自动安装（Windows 10/11）

如果您使用 Windows 10 或 11，可以使用 winget 自动安装：

```powershell
# 使用 winget 安装 Git
winget install --id Git.Git -e --source winget

# 验证安装
git --version

# 安装成功后运行部署脚本
cd C:\Users\Administrator\Desktop\zzd\task-manager
.\deploy.ps1
```

---

## 🎯 方案三：使用 Chocolatey 包管理器

如果您已安装 Chocolatey：

```powershell
# 安装 Chocolatey（如果未安装）
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# 使用 Chocolatey 安装 Git
choco install git -y

# 验证安装
git --version

# 运行部署脚本
cd C:\Users\Administrator\Desktop\zzd\task-manager
.\deploy.ps1
```

---

## 📝 Git 安装后的配置

安装 Git 后，需要配置用户名和邮箱：

```powershell
# 配置 Git 用户信息
git config --global user.name "liuGuanYi-hub"
git config --global user.email "your-email@example.com"

# 验证配置
git config --list
```

---

## ⚡ 快速部署流程

### 安装 Git 后，执行以下步骤：

```powershell
# 1. 进入项目目录
cd C:\Users\Administrator\Desktop\zzd\task-manager

# 2. 初始化 Git
git init

# 3. 添加所有文件
git add .

# 4. 提交代码
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

# 5. 设置主分支
git branch -M main

# 6. 关联远程仓库
git remote add origin https://github.com/liuGuanYi-hub/task-manager.git

# 7. 推送到 GitHub
# 需要输入 GitHub 用户名和 Personal Access Token
git push -u origin main
```

---

## 🔑 GitHub 认证

### 创建 Personal Access Token

1. 访问：https://github.com/settings/tokens
2. 点击 "Generate new token (classic)"
3. 填写备注（如：task-manager-deploy）
4. 勾选权限：✅ `repo` (Full control of private repositories)
5. 点击 "Generate token"
6. **复制并保存 Token**（只显示一次！）

### 使用 Token 推送

当提示输入密码时：
- **用户名**: 您的 GitHub 用户名
- **密码**: 使用 Personal Access Token（不是 GitHub 密码）

或者在 URL 中包含 Token：
```powershell
git push https://liuGuanYi-hub:YOUR_TOKEN@github.com/liuGuanYi-hub/task-manager.git
```

---

## 🆘 常见问题

### Q: 安装后 git 命令仍然不可用？

**A**: 重启 PowerShell 或终端窗口，让 PATH 环境变量生效。

### Q: 权限被拒绝？

**A**: 使用 Personal Access Token 代替密码，或配置 SSH 密钥。

### Q: 远程仓库不存在？

**A**: 先在 GitHub 创建空仓库 `task-manager`，不要初始化。

### Q: 推送大文件失败？

**A**: 安装 Git LFS：
```powershell
winget install GitHub.GitLFS
git lfs install
```

---

## 📞 需要帮助？

如果遇到问题：

1. **查看安装指南**: https://git-scm.com/book/en/v2/Getting-Started-Installing-Git
2. **GitHub 帮助**: https://docs.github.com/en/get-started/getting-started-with-git
3. **中文教程**: https://www.liaoxuefeng.com/wiki/896043488029600

---

## ✅ 完成检查

安装和部署完成后，应该能够：

- [ ] 运行 `git --version` 显示版本号
- [ ] 成功初始化 Git 仓库
- [ ] 成功提交代码
- [ ] 成功推送到 GitHub
- [ ] 访问 https://github.com/liuGuanYi-hub/task-manager 看到项目

---

**下一步**: 请先安装 Git，然后运行 `.\deploy.ps1` 完成部署！🚀
