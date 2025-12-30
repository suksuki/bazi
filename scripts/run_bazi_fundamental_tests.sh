#!/bin/bash
# BAZI_FUNDAMENTAL 注册表测试脚本
# 运行所有相关测试并生成报告

set -e

echo "=========================================="
echo "🧪 BAZI_FUNDAMENTAL 注册表测试套件"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试文件
TEST_FILE="tests/test_bazi_fundamental_registry.py"

# 检查测试文件是否存在
if [ ! -f "$TEST_FILE" ]; then
    echo -e "${RED}❌ 测试文件不存在: $TEST_FILE${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 测试文件存在${NC}"
echo ""

# 运行测试
echo "运行测试..."
python3 "$TEST_FILE" -v

# 检查退出码
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}=========================================="
    echo "✅ 所有测试通过！"
    echo "==========================================${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}=========================================="
    echo "❌ 测试失败！"
    echo "==========================================${NC}"
    exit 1
fi

