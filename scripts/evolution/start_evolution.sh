#!/bin/bash
# 启动自动进化脚本 (V50.1 Stagnation Breaker)

cd ~/bazi_predict || exit 1

echo "🚀 启动 Antigravity Auto-Evolve (V50.1 Stagnation Breaker)..."
echo "=========================================="
echo ""

# 检查并激活虚拟环境
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ 虚拟环境已激活"
else
    echo "❌ 错误: 虚拟环境 'venv' 不存在。"
    exit 1
fi
echo ""

# 停止旧进程（如果存在）
PID=$(ps aux | grep "[a]uto_evolve.py" | awk '{print $2}')
if [ -n "$PID" ]; then
    echo "🛑 停止旧进程 (PID: $PID)..."
    kill $PID
    sleep 2
    echo "✅ 旧进程已停止"
else
    echo "ℹ️  未发现旧进程运行"
fi
echo ""

# 启动新的自动进化进程
echo "🚀 启动新的自动进化进程..."
echo "   日志文件: evolution.log"
echo "   目标准确率: 82.0%"
echo "   模式: 无限循环直到达标"
echo "   新功能: Stagnation Breaker (僵局打破者)"
echo ""

nohup python3 scripts/auto_evolve.py > evolution.log 2>&1 &
NEW_PID=$!

echo "✅ 新进程已启动 (PID: $NEW_PID)"
echo ""

echo "📋 监控命令:"
echo "   查看实时日志: tail -f evolution.log"
echo "   检查状态: ps aux | grep auto_evolve"
echo "   停止脚本: kill $NEW_PID"
echo ""

# 等待几秒后显示初始输出
sleep 3
if [ -f "evolution.log" ]; then
    echo "📊 初始输出:"
    echo "----------------------------------------"
    tail -20 evolution.log
    echo "----------------------------------------"
fi
echo ""
echo "🎯 脚本已启动，将自动运行直到达到 82% 准确率！"
echo "💡 V50.1 新功能: 当检测到连续 5 次无改进时，会自动触发 CHAOS MODE 打破僵局"

