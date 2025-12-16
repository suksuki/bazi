#!/bin/bash
# 查看自动进化脚本的实时日志

cd /home/jin/bazi_predict || exit 1

if [ ! -f "evolution.log" ]; then
    echo "⚠️  日志文件不存在，脚本可能尚未启动"
    echo ""
    echo "启动命令:"
    echo "  bash scripts/start_evolution.sh"
    exit 1
fi

echo "=========================================="
echo "📊 Antigravity Auto-Evolve 实时日志"
echo "=========================================="
echo ""
echo "按 Ctrl+C 退出监控"
echo ""
echo "----------------------------------------"
tail -f evolution.log

