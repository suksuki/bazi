#!/bin/bash
# 检查参数调整状态

cd ~/bazi_predict || exit 1

echo "=========================================="
echo "📊 参数调整状态检查"
echo "=========================================="
echo ""

# 1. 检查进程状态
echo "1️⃣ 进程状态:"
PID=$(ps aux | grep "[a]uto_evolve.py" | awk '{print $2}')
if [ -n "$PID" ]; then
    RUNTIME=$(ps -p $PID -o etime= 2>/dev/null | tr -d ' ' || echo "未知")
    echo "   ✅ 自动进化脚本正在运行"
    echo "   PID: $PID"
    echo "   运行时间: $RUNTIME"
else
    echo "   ❌ 自动进化脚本未运行"
fi
echo ""

# 2. 检查参数文件中的关键参数
echo "2️⃣ 当前参数值（config/parameters.json）:"
if [ -f "config/parameters.json" ]; then
    echo "   flow.dampingFactor: $(python3 -c "import json; f=open('config/parameters.json'); d=json.load(f); print(d['flow']['dampingFactor'])")"
    echo "   flow.globalEntropy: $(python3 -c "import json; f=open('config/parameters.json'); d=json.load(f); print(d['flow']['globalEntropy'])")"
    echo "   flow.outputDrainPenalty: $(python3 -c "import json; f=open('config/parameters.json'); d=json.load(f); print(d['flow']['outputDrainPenalty'])")"
    echo ""
    echo "   参数范围上限（已更新）:"
    echo "   - dampingFactor: 0.0 → 0.6"
    echo "   - globalEntropy: 0.05 → 0.22"
    echo "   - outputDrainPenalty: 1.5 → 4.5"
else
    echo "   ⚠️  参数文件不存在"
fi
echo ""

# 3. 检查日志
echo "3️⃣ 最新日志:"
if [ -f "evolution.log" ]; then
    LOG_SIZE=$(stat -c%s "evolution.log" 2>/dev/null || echo "0")
    if [ "$LOG_SIZE" -gt 0 ]; then
        echo "   日志大小: $LOG_SIZE bytes"
        echo ""
        echo "   最后 15 行:"
        echo "   ----------------------------------------"
        tail -15 evolution.log | sed 's/^/   /'
        echo "   ----------------------------------------"
    else
        echo "   ⚠️  日志文件为空（脚本可能刚启动）"
    fi
else
    echo "   ⚠️  日志文件不存在"
fi
echo ""

# 4. 检查训练脚本中的参数范围
echo "4️⃣ 训练脚本参数范围（scripts/train_model_optuna.py）:"
if grep -q "flow.dampingFactor.*0.0, 0.6" scripts/train_model_optuna.py; then
    echo "   ✅ dampingFactor 范围已更新: 0.0 → 0.6"
else
    echo "   ⚠️  dampingFactor 范围可能未更新"
fi

if grep -q "flow.globalEntropy.*0.05, 0.22" scripts/train_model_optuna.py; then
    echo "   ✅ globalEntropy 范围已更新: 0.05 → 0.22"
else
    echo "   ⚠️  globalEntropy 范围可能未更新"
fi

if grep -q "flow.outputDrainPenalty.*1.5, 4.5" scripts/train_model_optuna.py; then
    echo "   ✅ outputDrainPenalty 范围已更新: 1.5 → 4.5"
else
    echo "   ⚠️  outputDrainPenalty 范围可能未更新"
fi
echo ""

# 5. 参数使用情况分析
echo "5️⃣ 参数使用情况分析:"
DAMPING=$(python3 -c "import json; f=open('config/parameters.json'); d=json.load(f); print(d['flow']['dampingFactor'])" 2>/dev/null)
ENTROPY=$(python3 -c "import json; f=open('config/parameters.json'); d=json.load(f); print(d['flow']['globalEntropy'])" 2>/dev/null)
DRAIN=$(python3 -c "import json; f=open('config/parameters.json'); d=json.load(f); print(d['flow']['outputDrainPenalty'])" 2>/dev/null)

if [ -n "$DAMPING" ]; then
    DAMPING_PCT=$(python3 -c "print(f'{($DAMPING / 0.6) * 100:.1f}')")
    echo "   dampingFactor: $DAMPING / 0.6 = ${DAMPING_PCT}% (上限使用率)"
fi

if [ -n "$ENTROPY" ]; then
    ENTROPY_PCT=$(python3 -c "print(f'{($ENTROPY / 0.22) * 100:.1f}')")
    echo "   globalEntropy: $ENTROPY / 0.22 = ${ENTROPY_PCT}% (上限使用率)"
    if (( $(echo "$ENTROPY >= 0.22" | bc -l) )); then
        echo "   ⚠️  globalEntropy 已达到上限！可能需要进一步扩大范围"
    fi
fi

if [ -n "$DRAIN" ]; then
    DRAIN_PCT=$(python3 -c "print(f'{($DRAIN / 4.5) * 100:.1f}')")
    echo "   outputDrainPenalty: $DRAIN / 4.5 = ${DRAIN_PCT}% (上限使用率)"
fi
echo ""

echo "💡 监控命令:"
echo "   实时日志: tail -f evolution.log"
echo "   停止脚本: kill $PID"

