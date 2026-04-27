# 自动部署脚本 - 一键推送到 GitHub
# 使用方法：.\deploy.ps1

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "🚀 任务管理系统 - 自动部署脚本" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 检查 Git 是否安装
Write-Host "📋 检查 Git 安装..." -ForegroundColor Yellow
try {
    $gitVersion = git --version
    Write-Host "✅ Git 已安装：$gitVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Git 未安装！" -ForegroundColor Red
    Write-Host "`n请先安装 Git: https://git-scm.com/download/win" -ForegroundColor Yellow
    Write-Host "`n按任意键退出..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# 进入项目目录
Write-Host "`n📁 进入项目目录..." -ForegroundColor Yellow
Set-Location -Path $PSScriptRoot

# 初始化 Git 仓库
Write-Host "`n📦 初始化 Git 仓库..." -ForegroundColor Yellow
if (Test-Path ".git") {
    Write-Host "ℹ️  Git 仓库已存在，跳过初始化" -ForegroundColor Gray
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
- Chart.js 数据可视化

#Python #Flask #TaskManager #WebApp"

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
Write-Host "⚠️  可能需要输入 GitHub 用户名和密码（或 Token）" -ForegroundColor Yellow
Write-Host "💡 提示：建议使用 Personal Access Token" -ForegroundColor Cyan
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
    Write-Host "`n解决方案请参考 GIT_SETUP.md`n" -ForegroundColor Cyan
}

Write-Host "📝 当前状态:" -ForegroundColor Cyan
git status
Write-Host ""
