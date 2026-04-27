# 自动化 Git 安装和部署脚本
# 此脚本会自动安装 Git 并完成部署

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "🚀 Git 自动安装和部署脚本" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 检查 Git 是否已安装
Write-Host "📋 检查 Git 安装状态..." -ForegroundColor Yellow
try {
    $null = Get-Command git -ErrorAction Stop
    Write-Host "✅ Git 已安装" -ForegroundColor Green
    $gitInstalled = $true
} catch {
    Write-Host "❌ Git 未安装" -ForegroundColor Red
    $gitInstalled = $false
}

if (-not $gitInstalled) {
    Write-Host "`n📦 开始安装 Git..." -ForegroundColor Yellow
    
    # 尝试使用 Chocolatey
    Write-Host "  尝试使用 Chocolatey 安装..." -ForegroundColor Gray
    try {
        $null = Get-Command choco -ErrorAction Stop
        Write-Host "  ✅ Chocolatey 已安装" -ForegroundColor Green
        Write-Host "  📥 正在安装 Git (这可能需要几分钟)..." -ForegroundColor Yellow
        choco install git -y --force
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ Git 安装成功！" -ForegroundColor Green
            Write-Host "`n  ⚠️  请重启 PowerShell 以使用 Git" -ForegroundColor Yellow
            Write-Host "  关闭此窗口，重新打开 PowerShell，然后运行：`n" -ForegroundColor Cyan
            Write-Host "  cd C:\Users\Administrator\Desktop\zzd\task-manager" -ForegroundColor White
            Write-Host "  .\deploy.ps1`n" -ForegroundColor White
            exit 0
        } else {
            Write-Host "  ❌ Chocolatey 安装失败" -ForegroundColor Red
        }
    } catch {
        Write-Host "  ❌ Chocolatey 未安装" -ForegroundColor Red
    }
    
    # 提供手动安装选项
    Write-Host "`n========================================" -ForegroundColor Yellow
    Write-Host "⚠️  需要手动安装 Git" -ForegroundColor Yellow
    Write-Host "========================================`n" -ForegroundColor Yellow
    
    Write-Host "请选择安装方式:`n" -ForegroundColor Cyan
    Write-Host "1. 下载安装 (推荐) - 访问 https://git-scm.com/download/win" -ForegroundColor White
    Write-Host "2. 使用 winget (Windows 10/11)" -ForegroundColor White
    Write-Host "3. 使用 Chocolatey" -ForegroundColor White
    
    Write-Host "`n 按任意键打开安装指南..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    
    # 打开浏览器到 Git 下载页面
    Start-Process "https://git-scm.com/download/win"
    
    Write-Host "`n📝 安装步骤:" -ForegroundColor Cyan
    Write-Host "  1. 下载 Git 安装程序" -ForegroundColor White
    Write-Host "  2. 运行安装程序，一直点击 Next" -ForegroundColor White
    Write-Host "  3. 选择 'Git from the command line'" -ForegroundColor White
    Write-Host "  4. 完成安装" -ForegroundColor White
    Write-Host "  5. 重启 PowerShell" -ForegroundColor White
    Write-Host "  6. 运行命令：git --version" -ForegroundColor White
    
    Write-Host "`n 安装完成后，运行部署脚本：" -ForegroundColor Cyan
    Write-Host "  cd C:\Users\Administrator\Desktop\zzd\task-manager" -ForegroundColor White
    Write-Host "  .\deploy.ps1`n" -ForegroundColor White
    
    exit 1
}

# Git 已安装，继续部署流程
Write-Host "`n========================================" -ForegroundColor Green
Write-Host "✅ Git 已就绪，开始部署..." -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Green

# 配置 Git 用户信息
Write-Host "📝 配置 Git 用户信息..." -ForegroundColor Yellow
$username = Read-Host "输入 GitHub 用户名"
$email = Read-Host "输入邮箱地址"

git config --global user.name $username
git config --global user.email $email

Write-Host "✅ Git 配置完成" -ForegroundColor Green

# 初始化 Git 仓库
Write-Host "`n📦 初始化 Git 仓库..." -ForegroundColor Yellow
if (Test-Path ".git") {
    Write-Host "ℹ️  Git 仓库已存在" -ForegroundColor Gray
} else {
    git init
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Git 仓库初始化完成" -ForegroundColor Green
    } else {
        Write-Host "❌ Git 仓库初始化失败" -ForegroundColor Red
        exit 1
    }
}

# 添加所有文件
Write-Host "`n📝 添加所有文件..." -ForegroundColor Yellow
git add .
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 文件添加成功" -ForegroundColor Green
} else {
    Write-Host "❌ 文件添加失败" -ForegroundColor Red
    exit 1
}

# 提交代码
Write-Host "`n💾 提交代码..." -ForegroundColor Yellow
$commitMessage = "Initial commit: 个人任务管理系统 v1.0

功能包括:
- 命令行任务管理 (CRUD)
- 任务搜索和过滤
- 统计报表和周报
- 任务提醒功能
- Web 界面 (Flask)
- 完整的单元测试
- 多页面统计仪表板
- Chart.js 数据可视化"

git commit -m $commitMessage
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 代码提交成功" -ForegroundColor Green
} else {
    Write-Host "⚠️  提交失败（可能是空提交或没有变更）" -ForegroundColor Yellow
}

# 设置主分支
Write-Host "`n🔀 设置主分支..." -ForegroundColor Yellow
git branch -M main
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 主分支设置完成" -ForegroundColor Green
} else {
    Write-Host "⚠️  分支设置失败（可能已存在）" -ForegroundColor Gray
}

# 关联远程仓库
Write-Host "`n🔗 关联远程仓库..." -ForegroundColor Yellow
$remoteUrl = "https://github.com/liuGuanYi-hub/task-manager.git"

# 检查是否已存在 origin
$existingRemote = git remote get-url origin 2>$null
if ($existingRemote) {
    Write-Host "ℹ️  远程仓库已存在：$existingRemote" -ForegroundColor Gray
    $change = Read-Host "是否更改为 $remoteUrl? (y/n)"
    if ($change -eq 'y' -or $change -eq 'Y') {
        git remote set-url origin $remoteUrl
    }
} else {
    git remote add origin $remoteUrl
    Write-Host "✅ 远程仓库关联成功" -ForegroundColor Green
}

# 推送代码
Write-Host "`n📤 推送到 GitHub..." -ForegroundColor Yellow
Write-Host "⚠️  需要输入 GitHub 认证信息" -ForegroundColor Yellow
Write-Host "💡 提示：使用 Personal Access Token" -ForegroundColor Cyan
Write-Host "   创建地址：https://github.com/settings/tokens`n" -ForegroundColor Cyan

git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "🎉 部署成功！" -ForegroundColor Green
    Write-Host "========================================`n" -ForegroundColor Green
    Write-Host "🌐 访问项目：" -ForegroundColor Cyan
    Write-Host "   https://github.com/liuGuanYi-hub/task-manager`n" -ForegroundColor White
    Write-Host "📊 查看提交：" -ForegroundColor Cyan
    Write-Host "   https://github.com/liuGuanYi-hub/task-manager/commits/main`n" -ForegroundColor White
} else {
    Write-Host "`n========================================" -ForegroundColor Red
    Write-Host "❌ 推送失败" -ForegroundColor Red
    Write-Host "========================================`n" -ForegroundColor Red
    Write-Host "可能的原因:" -ForegroundColor Yellow
    Write-Host "  1. 认证失败（需要 Token 或 SSH 密钥）" -ForegroundColor Gray
    Write-Host "  2. 远程仓库不存在" -ForegroundColor Gray
    Write-Host "  3. 网络连接问题" -ForegroundColor Gray
    Write-Host "`n解决方案请参考 INSTALL_GIT_AND_DEPLOY.md`n" -ForegroundColor Cyan
}

Write-Host "📝 当前状态:" -ForegroundColor Cyan
git status
Write-Host ""
