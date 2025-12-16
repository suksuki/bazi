#!/bin/bash
# 重启自动进化脚本 (V50.1 Stagnation Breaker)

cd ~/bazi_predict || exit 1

echo "🔄 重启 Antigravity Auto-Evolve (V50.1 Stagnation Breaker)..."
echo "=========================================="
echo ""

# 1. 检查并停止旧进程
PID=$(ps aux | grep "[a]uto_evolve.py" | awk '{print $2}')
if [ -n "$PID" ]; then
    echo "🛑 停止旧进程 (PID: $PID)..."
    kill $PID 2>/dev/null || true
    sleep 2
    
    # 确保进程已停止
    if ps -p $PID > /dev/null 2>&1; then
        echo "⚠️  进程仍在运行，强制停止..."
        kill -9 $PID 2>/dev/null || true
        sleep 1
    fi
    echo "✅ 旧进程已停止"
else
    echo "ℹ️  没有运行中的进程"
fi
echo ""

# 2. 确认参数范围已更新
echo "📋 检查参数范围更新..."
if grep -q "0.0, 0.6" scripts/train_model_optuna.py && \
   grep -q "0.05, 0.22" scripts/train_model_optuna.py && \
   grep -q "1.5, 4.5" scripts/train_model_optuna.py; then
    echo "✅ 参数范围已更新："
    echo "   - dampingFactor: 0.0 → 0.6"
    echo "   - globalEntropy: 0.05 → 0.22"
    echo "   - outputDrainPenalty: 1.5 → 4.5"
else
    echo "⚠️  参数范围可能未完全更新，请检查 train_model_optuna.py"
fi
echo ""

# 3. 激活虚拟环境
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ 虚拟环境已激活"
else
    echo "⚠️  虚拟环境不存在，使用系统 Python"
fi
echo ""

# 4. 启动新进程
echo "🚀 启动新的自动进化进程..."
echo "   日志文件: evolution.log"
echo "   目标准确率: 82.0%"
echo "   模式: 无限循环直到达标"
echo "   新功能: Stagnation Breaker (僵局打破者)"
echo "   - 自动检测连续 5 次无改进"
echo "   - 触发 CHAOS MODE: 极端权重偏向 + 参数抖动 + 超大范围"
echo ""

# 使用 nohup 在后台运行
nohup python3 scripts/auto_evolve.py > evolution.log 2>&1 &
NEW_PID=$!

echo "✅ 新进程已启动 (PID: $NEW_PID)"
echo ""
echo "📋 监控命令:"
echo "   查看实时日志: tail -f evolution.log"
echo "   检查状态: bash scripts/check_evolution_status.sh"
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
echo "🎯 现在脚本将使用更新后的参数范围继续优化！"
echo "💡 V50.1 新功能: 当检测到连续 5 次无改进时，会自动触发 CHAOS MODE 打破僵局"

