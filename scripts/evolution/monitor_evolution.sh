#!/bin/bash
# 监控自动进化脚本的运行状态

echo "=========================================="
echo "🔍 Antigravity Auto-Evolve 监控工具"
echo "=========================================="
echo ""

# 检查进程是否运行
PID=$(ps aux | grep "auto_evolve.py" | grep -v grep | awk '{print $2}')
if [ -z "$PID" ]; then
    echo "❌ 自动进化脚本未运行"
    echo ""
    echo "启动命令:"
    echo "  nohup python3 scripts/auto_evolve.py > evolution.log 2>&1 &"
    exit 1
else
    echo "✅ 自动进化脚本正在运行 (PID: $PID)"
fi
echo ""

# 显示日志文件信息
if [ -f "evolution.log" ]; then
    log_size=$(stat -f%z "evolution.log" 2>/dev/null || stat -c%s "evolution.log" 2>/dev/null || echo "unknown")
    echo "📄 日志文件: evolution.log"
    echo "   大小: $log_size bytes"
    echo ""
    
    # 显示最后几行
    echo "📊 最新日志 (最后 20 行):"
    echo "----------------------------------------"
    tail -20 evolution.log
    echo "----------------------------------------"
    echo ""
    
    # 提取关键信息
    echo "📈 关键指标:"
    echo "----------------------------------------"
    
    # 总准确率
    total_acc=$(grep "总准确率:" evolution.log | tail -1 | grep -oE "[0-9]+\.[0-9]+%" | head -1)
    if [ -n "$total_acc" ]; then
        echo "   当前总准确率: $total_acc"
    fi
    
    # 迭代次数
    iteration=$(grep "迭代" evolution.log | tail -1 | grep -oE "[0-9]+/[0-9]+" | head -1)
    if [ -n "$iteration" ]; then
        echo "   当前迭代: $iteration"
    fi
    
    # 最佳准确率
    best_acc=$(grep "当前最佳准确率:" evolution.log | tail -1 | grep -oE "[0-9]+\.[0-9]+%" | head -1)
    if [ -n "$best_acc" ]; then
        echo "   最佳准确率: $best_acc"
    fi
    
    echo "----------------------------------------"
else
    echo "⚠️  日志文件不存在"
fi
echo ""

# 显示参数文件修改时间
if [ -f "config/parameters.json" ]; then
    mod_time=$(stat -f "%Sm" "config/parameters.json" 2>/dev/null || stat -c "%y" "config/parameters.json" 2>/dev/null | cut -d'.' -f1)
    echo "📝 参数文件最后修改: $mod_time"
fi
echo ""

echo "💡 实时监控命令:"
echo "   tail -f evolution.log"
echo ""
echo "🛑 停止脚本命令:"
echo "   kill $PID"

