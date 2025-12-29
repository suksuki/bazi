#!/bin/bash
# 全息格局V2.1自动化测试运行脚本

echo "======================================================================"
echo "🚀 全息格局V2.1自动化测试套件"
echo "======================================================================"
echo ""

cd "$(dirname "$0")/.." || exit 1

# 运行测试
python3 tests/test_holographic_pattern_v21.py

# 检查退出码
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 所有测试通过！"
    exit 0
else
    echo ""
    echo "❌ 部分测试失败，请检查上述错误信息"
    exit 1
fi

