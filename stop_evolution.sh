#!/bin/bash
# 停止所有 auto_evolve.py 进程

cd ~/bazi_predict || exit 1

echo "🛑 查找并停止所有 auto_evolve.py 进程..."
echo ""

# 查找所有相关进程
PIDS=$(ps aux | grep "[a]uto_evolve.py" | awk '{print $2}')

if [ -z "$PIDS" ]; then
    echo "✅ 没有运行中的 auto_evolve.py 进程"
    exit 0
fi

echo "找到以下进程:"
ps aux | grep "[a]uto_evolve.py" | grep -v grep
echo ""

# 逐个停止
for PID in $PIDS; do
    echo "停止进程 PID: $PID"
    kill $PID 2>/dev/null
    sleep 1
    
    # 检查是否还在运行
    if ps -p $PID > /dev/null 2>&1; then
        echo "  强制停止 PID: $PID"
        kill -9 $PID 2>/dev/null
        sleep 1
    fi
    
    # 再次确认
    if ps -p $PID > /dev/null 2>&1; then
        echo "  ⚠️  进程 $PID 仍在运行"
    else
        echo "  ✅ 进程 $PID 已停止"
    fi
done

echo ""
echo "最终检查..."
REMAINING=$(ps aux | grep "[a]uto_evolve.py" | grep -v grep | wc -l)
if [ "$REMAINING" -eq 0 ]; then
    echo "✅ 所有进程已停止"
else
    echo "⚠️  仍有 $REMAINING 个进程在运行"
    ps aux | grep "[a]uto_evolve.py" | grep -v grep
fi

