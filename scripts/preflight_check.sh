#!/bin/bash
# 发射前检查脚本 (Pre-Flight Check Script)
# 用于在运行 auto_evolve.py 之前进行安全检查

echo "=========================================="
echo "🛡️  Antigravity Auto-Evolve 发射前检查"
echo "=========================================="
echo ""

# 1. 检查备份文件是否存在
echo "1️⃣  检查黄金存档备份..."
if [ -f "config/parameters_v49_golden.json" ]; then
    echo "   ✅ 找到备份文件: config/parameters_v49_golden.json"
    backup_size=$(stat -f%z "config/parameters_v49_golden.json" 2>/dev/null || stat -c%s "config/parameters_v49_golden.json" 2>/dev/null || echo "unknown")
    echo "   📊 备份文件大小: $backup_size bytes"
else
    echo "   ⚠️  未找到备份文件，正在创建..."
    cp config/parameters.json config/parameters_v49_golden.json
    echo "   ✅ 备份已创建"
fi
echo ""

# 2. 检查必要文件是否存在
echo "2️⃣  检查必要文件..."
files=(
    "scripts/auto_evolve.py"
    "scripts/train_model_optuna.py"
    "scripts/batch_verify.py"
    "config/parameters.json"
    "data/golden_cases.json"
)

all_exist=true
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ $file (缺失)"
        all_exist=false
    fi
done

if [ "$all_exist" = false ]; then
    echo ""
    echo "❌ 部分必要文件缺失，请检查后重试"
    exit 1
fi
echo ""

# 3. 检查 Git 状态（如果可用）
echo "3️⃣  检查 Git 状态..."
if command -v git &> /dev/null && [ -d ".git" ]; then
    git_status=$(git status --porcelain config/parameters.json 2>/dev/null)
    if [ -z "$git_status" ]; then
        echo "   ✅ config/parameters.json 未被修改"
    else
        echo "   ⚠️  config/parameters.json 有未提交的更改"
        echo "   建议: git diff config/parameters.json"
    fi
else
    echo "   ⚠️  Git 不可用或未初始化（非必需）"
fi
echo ""

# 4. 检查 Python 环境
echo "4️⃣  检查 Python 环境..."
if command -v python3 &> /dev/null; then
    python_version=$(python3 --version)
    echo "   ✅ $python_version"
    
    # 检查必要的 Python 包
    echo "   检查必要包..."
    if python3 -c "import optuna" 2>/dev/null; then
        echo "      ✅ optuna"
    else
        echo "      ❌ optuna (缺失)"
        echo "      ⚠️  请运行: pip install optuna"
    fi
else
    echo "   ❌ Python3 未找到"
    exit 1
fi
echo ""

# 5. 显示当前配置摘要
echo "5️⃣  当前配置摘要..."
if [ -f "config/parameters.json" ]; then
    echo "   关键参数:"
    
    # 使用 Python 提取关键参数
    python3 << 'EOF'
import json
try:
    with open("config/parameters.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    
    # 显示关键参数
    if "structure" in config and "rootingWeight" in config["structure"]:
        print(f"      rootingWeight: {config['structure']['rootingWeight']:.2f}")
    if "flow" in config:
        flow = config["flow"]
        if "controlImpact" in flow:
            print(f"      controlImpact: {flow['controlImpact']:.2f}")
        if "outputDrainPenalty" in flow:
            print(f"      outputDrainPenalty: {flow['outputDrainPenalty']:.2f}")
        if "earthMetalMoistureBoost" in flow:
            print(f"      earthMetalMoistureBoost: {flow['earthMetalMoistureBoost']:.2f}")
except Exception as e:
    print(f"      ⚠️  无法读取配置: {e}")
EOF
fi
echo ""

echo "=========================================="
echo "✅ 检查完成！"
echo "=========================================="
echo ""
echo "📋 建议的运行命令:"
echo "   试运行: python3 scripts/auto_evolve.py --target 80.0 --max-iter 2"
echo "   正式运行: python3 scripts/auto_evolve.py > evolution.log 2>&1 &"
echo ""
echo "🚀 准备好了吗？Good luck, Commander!"

