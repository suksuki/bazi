#!/bin/bash
# 运行 GraphNetworkEngine 重构测试脚本
# ======================================

echo "=========================================="
echo "GraphNetworkEngine 重构测试"
echo "=========================================="
echo ""

# 进入项目根目录
cd "$(dirname "$0")/.."

# 运行测试
echo "运行自动化测试..."
python -m unittest tests.test_engine_graph_refactoring -v

# 检查退出码
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 所有测试通过！"
    exit 0
else
    echo ""
    echo "❌ 测试失败！"
    exit 1
fi

