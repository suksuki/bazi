#!/bin/bash
# 停止旧进程并重启 V53.0 Step 1: Foundation Locking Tuning

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

# 也停止 train_model_optuna.py（如果单独运行）
PID2=$(ps aux | grep "[t]rain_model_optuna.py" | awk '{print $2}')
if [ -n "$PID2" ]; then
    echo "   找到 train_model_optuna.py 进程 PID: $PID2"
    kill $PID2 2>/dev/null
    sleep 1
    if ps -p $PID2 > /dev/null 2>&1; then
        kill -9 $PID2 2>/dev/null
    fi
    echo "   ✅ train_model_optuna.py 已停止"
fi
echo ""

echo "🚀 启动 V53.0 Step 1: Foundation Locking Tuning..."
echo "   版本: Controlled Float - Foundation Only"
echo "   模式: 仅优化基础物理层，锁死 Flow 和 Interactions"
echo "   新功能: 每轮训练后显示准确率"
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
echo "   V53.0 Step 1: 仅优化 Foundation"
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
echo "🎯 V53.0 Step 1: Foundation Locking Tuning 已启动！"
echo "   - 仅优化 Group 1 (Foundation): pillarWeights, rootingWeight"
echo "   - Group 2 (Flow) 和 Group 3 (Interactions) 已锁死"
echo "   - 每轮训练后会显示准确率"

