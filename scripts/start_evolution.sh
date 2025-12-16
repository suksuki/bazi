#!/bin/bash
# 启动自动进化脚本（后台运行）

cd /home/jin/bazi_predict || exit 1

# 检查是否已经在运行
if ps aux | grep -q "[a]uto_evolve.py"; then
    echo "⚠️  自动进化脚本已在运行"
    ps aux | grep "[a]uto_evolve.py" | grep -v grep
    exit 1
fi

# 激活虚拟环境并启动脚本
source venv/bin/activate

echo "🚀 启动 Antigravity Auto-Evolve..."
echo "   日志文件: evolution.log"
echo ""

# 使用 nohup 在后台运行
nohup python3 scripts/auto_evolve.py > evolution.log 2>&1 &
PID=$!

echo "✅ 脚本已启动 (PID: $PID)"
echo ""
echo "📋 监控命令:"
echo "   查看日志: tail -f evolution.log"
echo "   检查状态: bash scripts/check_evolution_status.sh"
echo "   停止脚本: kill $PID"
echo ""

# 等待几秒后显示初始输出
sleep 3
if [ -f "evolution.log" ]; then
    echo "📊 初始输出:"
    echo "----------------------------------------"
    tail -20 evolution.log
    echo "----------------------------------------"
fi

