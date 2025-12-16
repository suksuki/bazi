#!/bin/bash
# 快速检查自动进化脚本的状态

cd /home/jin/bazi_predict || exit 1

echo "=========================================="
echo "🔍 Antigravity Auto-Evolve 状态检查"
echo "=========================================="
echo ""

# 1. 检查进程
PID=$(ps aux | grep "[a]uto_evolve.py" | awk '{print $2}')
if [ -n "$PID" ]; then
    echo "✅ 脚本正在运行 (PID: $PID)"
    echo "   运行时间: $(ps -p $PID -o etime= 2>/dev/null || echo "未知")"
else
    echo "❌ 脚本未运行"
fi
echo ""

# 2. 检查日志
if [ -f "evolution.log" ]; then
    echo "📄 日志文件: evolution.log"
    log_size=$(stat -f%z "evolution.log" 2>/dev/null || stat -c%s "evolution.log" 2>/dev/null || echo "unknown")
    echo "   大小: $log_size bytes"
    echo ""
    
    # 提取关键信息
    echo "📊 最新状态:"
    echo "----------------------------------------"
    
    # 最新迭代
    latest_iter=$(grep "迭代" evolution.log | tail -1)
    if [ -n "$latest_iter" ]; then
        echo "   $latest_iter"
    fi
    
    # 最新准确率
    latest_acc=$(grep "总准确率:" evolution.log | tail -1)
    if [ -n "$latest_acc" ]; then
        echo "   $latest_acc"
    fi
    
    # 最佳准确率
    best_acc=$(grep "当前最佳准确率:" evolution.log | tail -1)
    if [ -n "$best_acc" ]; then
        echo "   $best_acc"
    fi
    
    # 权重调整
    latest_weights=$(grep "动态权重调整" evolution.log -A 3 | tail -3)
    if [ -n "$latest_weights" ]; then
        echo ""
        echo "   最新权重调整:"
        echo "$latest_weights" | sed 's/^/      /'
    fi
    
    echo "----------------------------------------"
    echo ""
    echo "📋 最后 10 行日志:"
    echo "----------------------------------------"
    tail -10 evolution.log | sed 's/^/   /'
else
    echo "⚠️  日志文件不存在（脚本可能在前台运行）"
fi
echo ""

# 3. 检查参数文件
if [ -f "config/parameters.json" ]; then
    mod_time=$(stat -f "%Sm" "config/parameters.json" 2>/dev/null || stat -c "%y" "config/parameters.json" 2>/dev/null | cut -d'.' -f1)
    echo "📝 参数文件最后修改: $mod_time"
fi
echo ""

echo "💡 实时监控: tail -f evolution.log"
echo "🛑 停止脚本: kill $PID"

