#!/bin/bash
# 安全的 Git 推送脚本（带超时和错误处理）

cd /home/jin/bazi_predict || exit 1

echo "=========================================="
echo "🚀 Git 安全推送"
echo "=========================================="
echo ""

# 检查是否有未提交的更改
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  检测到未提交的更改"
    echo ""
    echo "请先提交更改，然后再推送："
    echo "  git add <files>"
    echo "  git commit -m 'message'"
    echo "  git push origin main"
    exit 1
fi

# 检查本地和远程的差异
echo "📊 检查本地和远程的差异..."
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main 2>/dev/null || echo "")

if [ -z "$REMOTE" ]; then
    echo "   ⚠️  无法获取远程分支信息，可能需要先 fetch"
    git fetch origin
    REMOTE=$(git rev-parse origin/main 2>/dev/null || echo "")
fi

if [ "$LOCAL" = "$REMOTE" ]; then
    echo "   ✅ 本地和远程已同步，无需推送"
    exit 0
fi

echo "   本地: $LOCAL"
echo "   远程: $REMOTE"
echo ""

# 显示将要推送的提交
echo "📝 将要推送的提交:"
git log origin/main..HEAD --oneline | head -10
echo ""

# 询问确认（在非交互模式下自动确认）
if [ -t 0 ]; then
    read -p "确认推送？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "已取消"
        exit 1
    fi
fi

# 执行推送（带超时）
echo "🚀 开始推送..."
if timeout 30 git push origin main 2>&1; then
    echo ""
    echo "✅ 推送成功！"
    git status
else
    EXIT_CODE=$?
    echo ""
    if [ $EXIT_CODE -eq 124 ]; then
        echo "⏱️  推送超时（30秒）"
        echo ""
        echo "可能的原因："
        echo "1. 需要身份验证（用户名/密码或 token）"
        echo "2. 网络连接问题"
        echo "3. 远程仓库访问受限"
        echo ""
        echo "建议："
        echo "- 使用 GitLens 插件在 VS Code 中推送（支持图形化认证）"
        echo "- 或配置 SSH 密钥"
        echo "- 或使用 GitHub CLI: gh auth login"
    else
        echo "❌ 推送失败（退出码: $EXIT_CODE）"
    fi
    exit $EXIT_CODE
fi

