#!/bin/bash
# Git 历史问题彻底解决脚本
# 目标：解决所有冲突，清理历史，同步本地和远程

set -e  # 遇到错误立即退出

cd /home/jin/bazi_predict || exit 1

echo "=========================================="
echo "🔧 Git 历史问题彻底解决"
echo "=========================================="
echo ""

# 步骤 1: 检查当前状态
echo "📋 步骤 1: 检查当前 Git 状态..."
git status --short | head -20
echo ""

# 步骤 2: 获取远程最新状态
echo "📥 步骤 2: 获取远程最新状态..."
git fetch origin
echo ""

# 步骤 3: 检查是否有冲突
echo "🔍 步骤 3: 检查合并冲突..."
if git merge-base --is-ancestor HEAD origin/main 2>/dev/null; then
    echo "   ✅ 本地分支是远程分支的祖先，可以安全合并"
elif git merge-base --is-ancestor origin/main HEAD 2>/dev/null; then
    echo "   ⚠️  本地分支领先远程分支，需要推送"
else
    echo "   ⚠️  本地和远程分支已分叉，需要合并"
fi
echo ""

# 步骤 4: 显示差异统计
echo "📊 步骤 4: 差异统计..."
echo "   修改的文件: $(git diff --name-only | wc -l)"
echo "   未跟踪的文件: $(git ls-files --others --exclude-standard | wc -l)"
echo ""

echo "=========================================="
echo "✅ 状态检查完成"
echo "=========================================="
echo ""
echo "下一步操作建议："
echo "1. 添加所有重要文件: git add <files>"
echo "2. 提交更改: git commit -m 'message'"
echo "3. 拉取远程: git pull origin main (如果有冲突需要解决)"
echo "4. 推送本地: git push origin main"

