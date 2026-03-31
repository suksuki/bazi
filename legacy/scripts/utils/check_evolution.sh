#!/bin/bash
# 快速检查自动进化脚本状态

cd ~/bazi_predict || exit 1

echo "=========================================="
echo "🔍 Antigravity Auto-Evolve 状态检查"
echo "=========================================="
echo ""

# 1. 检查进程
PID=$(ps aux | grep "[a]uto_evolve.py" | awk '{print $2}')
if [ -n "$PID" ]; then
    echo "✅ 脚本正在运行 (PID: $PID)"
    ETIME=$(ps -p $PID -o etime= 2>/dev/null | tr -d ' ')
    CPU=$(ps -p $PID -o %cpu= 2>/dev/null | tr -d ' ')
    MEM=$(ps -p $PID -o %mem= 2>/dev/null | tr -d ' ')
    echo "   运行时间: $ETIME"
    echo "   CPU 使用: ${CPU}%"
    echo "   内存使用: ${MEM}%"
else
    echo "❌ 脚本未运行"
    exit 1
fi
echo ""

# 2. 检查日志文件
if [ -f "evolution.log" ]; then
    LOG_SIZE=$(wc -c < evolution.log 2>/dev/null || echo "0")
    LOG_LINES=$(wc -l < evolution.log 2>/dev/null || echo "0")
    echo "📄 日志文件: evolution.log"
    echo "   大小: $LOG_SIZE bytes"
    echo "   行数: $LOG_LINES lines"
    echo ""
    
    if [ "$LOG_LINES" -gt 2 ]; then
        echo "📊 最新日志 (最后 30 行):"
        echo "----------------------------------------"
        tail -30 evolution.log
        echo "----------------------------------------"
    else
        echo "⚠️  日志内容很少，脚本可能还在初始化..."
        echo "   当前内容:"
        cat evolution.log
        echo ""
        echo "💡 建议: 等待几分钟后再次检查，或使用 'tail -f evolution.log' 实时查看"
    fi
else
    echo "⚠️  日志文件不存在"
fi
echo ""

# 3. 检查是否有错误输出
if [ -f "nohup.out" ]; then
    echo "📄 发现 nohup.out 文件:"
    tail -20 nohup.out
    echo ""
fi

# 4. 检查参数文件
if [ -f "config/parameters.json" ]; then
    MOD_TIME=$(stat -c %y config/parameters.json 2>/dev/null || stat -f %Sm config/parameters.json 2>/dev/null || echo "未知")
    echo "📋 参数文件: config/parameters.json"
    echo "   最后修改: $MOD_TIME"
fi
echo ""

echo "📋 监控命令:"
echo "   实时查看日志: tail -f evolution.log"
echo "   停止脚本: kill $PID"
echo "   查看完整日志: less evolution.log"

