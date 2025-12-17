#!/bin/bash
# 停止旧进程并重启 V51.0 Fine-Tuning Mode

cd ~/bazi_predict || exit 1

echo "🛑 停止旧的 auto_evolve.py 进程..."
PID=$(ps aux | grep "[a]uto_evolve.py" | awk '{print $2}')
if [ -n "$PID" ]; then
    echo "   找到进程 PID: $PID"
    kill $PID 2>/dev/null
    sleep 2
    if ps -p $PID > /dev/null 2>&1; then
        echo "   强制停止..."
        kill -9 $PID 2>/dev/null
    fi
    echo "   ✅ 旧进程已停止"
else
    echo "   ℹ️  没有运行中的进程"
fi
echo ""

echo "🚀 启动 V52.0 Fine-Tuning Mode..."
echo "   版本: Golden Ratio Hard-Reset + Net Force Settlement"
echo "   模式: 锁定核心参数，只调整边缘参数"
echo "   新功能: 显式净作用力计算（解决 Balanced 误判）"
echo ""

# 激活虚拟环境
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ 虚拟环境已激活"
else
    echo "⚠️  虚拟环境不存在，使用系统 Python"
fi
echo ""

# 启动新进程
echo "📋 启动参数:"
echo "   目标准确率: 82.0%"
echo "   模式: 无限循环直到达标"
echo "   日志文件: evolution.log"
echo ""

nohup python3 scripts/auto_evolve.py > evolution.log 2>&1 &
NEW_PID=$!

echo "✅ 新进程已启动 (PID: $NEW_PID)"
echo ""
echo "📋 监控命令:"
echo "   查看实时日志: tail -f evolution.log"
echo "   检查状态: ps -p $NEW_PID"
echo "   停止脚本: kill $NEW_PID"
echo ""

# 等待几秒后显示初始输出
sleep 3
if [ -f "evolution.log" ]; then
    echo "📊 初始输出:"
    echo "----------------------------------------"
    tail -30 evolution.log
    echo "----------------------------------------"
fi

echo ""
echo "🎯 V52.0 Fine-Tuning Mode 已启动！"
echo "   核心参数已锁定（黄金比例）"
echo "   只调整边缘参数：earthMetalMoistureBoost, clashDamping"
echo "   ✅ 新功能：显式净作用力计算（Net Force Settlement）"
echo "      - 自动识别受力平衡态"
echo "      - 解决 Balanced 案例误判"

