#!/bin/bash
# 检查当前训练阶段状态

cd /home/jin/bazi_predict || exit 1

echo "🔍 检查当前训练状态..."
echo ""

# 检查是否有运行中的进程
PID=$(ps aux | grep "[a]uto_evolve.py" | awk '{print $2}')
if [ -n "$PID" ]; then
    echo "✅ 发现运行中的进程: PID $PID"
    echo "   命令行:"
    ps aux | grep "[a]uto_evolve.py" | grep -v grep
    echo ""
    
    # 检查命令行参数
    if ps aux | grep "[a]uto_evolve.py" | grep -q "step.*2"; then
        echo "🎯 当前运行: Step 2 (Dynamics Only)"
    elif ps aux | grep "[a]uto_evolve.py" | grep -q "step.*1"; then
        echo "🎯 当前运行: Step 1 (Foundation Only)"
    else
        echo "🎯 当前运行: Step 1 (默认，未指定 --step)"
    fi
else
    echo "ℹ️  没有运行中的 auto_evolve.py 进程"
fi
echo ""

# 检查日志中的最新阶段信息
echo "📋 日志中的最新阶段信息:"
if [ -f "evolution.log" ]; then
    # 查找最后出现的阶段信息
    LAST_STEP=$(tail -500 evolution.log | grep -E "Step [12]|Dynamics Only|Foundation Only" | tail -1)
    if [ -n "$LAST_STEP" ]; then
        echo "   $LAST_STEP"
    else
        echo "   ⚠️  日志中未找到阶段信息（可能是旧日志）"
    fi
    echo ""
    
    # 显示最后几行日志
    echo "📄 最新日志 (最后 10 行):"
    tail -10 evolution.log
else
    echo "   ⚠️  日志文件不存在"
fi
echo ""

echo "💡 如何切换到 Step 2:"
echo "   1. 停止当前进程: pkill -f auto_evolve.py"
echo "   2. 启动 Step 2: python3 scripts/auto_evolve.py --step 2"
echo "   或者使用: bash restart_v53_step1.sh (需要修改为 --step 2)"
echo ""

