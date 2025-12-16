#!/bin/bash
# Git 引用修复脚本
# 解决 origin/HEAD 和 origin/main 找不到的问题

cd "$(dirname "$0")/.." || exit 1

echo "=========================================="
echo "🔧 Git 引用修复脚本"
echo "=========================================="
echo ""

# 1. 清理并重新获取远程引用
echo "📥 步骤 1: 获取并清理远程引用..."
git fetch --all --prune
echo ""

# 2. 显示远程信息
echo "📊 步骤 2: 检查远程配置..."
git remote show origin
echo ""

# 3. 显示远程分支
echo "🌿 步骤 3: 检查远程分支..."
git branch -r
echo ""

# 4. 自动设置 origin/HEAD
echo "🎯 步骤 4: 设置 origin/HEAD..."
git remote set-head origin -a
echo ""

# 5. 验证 origin/HEAD
echo "✅ 步骤 5: 验证修复结果..."
if git symbolic-ref refs/remotes/origin/HEAD >/dev/null 2>&1; then
    echo "   ✅ origin/HEAD 已正确设置:"
    git symbolic-ref refs/remotes/origin/HEAD
else
    echo "   ❌ origin/HEAD 设置失败"
    exit 1
fi
echo ""

# 6. 检查本地分支跟踪
echo "🔗 步骤 6: 检查本地分支跟踪..."
git branch -vv
echo ""

# 7. 检查远程引用文件
echo "📁 步骤 7: 检查远程引用文件..."
if [ -d .git/refs/remotes/origin ]; then
    echo "   ✅ 远程引用目录存在:"
    ls -la .git/refs/remotes/origin/
else
    echo "   ⚠️  远程引用目录不存在"
fi
echo ""

echo "=========================================="
echo "✅ 修复完成！"
echo "=========================================="
echo ""
echo "如果 VS Code 仍然报错，请："
echo "1. 重启 VS Code"
echo "2. 或在 VS Code 设置中关闭 'Git: Auto Fetch'"
echo ""

