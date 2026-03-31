#!/bin/bash

echo "🔍 诊断 APP 启动问题..."
echo "================================"
echo ""

# 1. 检查虚拟环境
echo "1️⃣ 检查虚拟环境..."
if [ ! -d "venv" ]; then
    echo "   ❌ 虚拟环境不存在！"
    echo "   请运行: python3 -m venv venv"
    exit 1
else
    echo "   ✅ 虚拟环境存在"
fi

# 2. 检查 Python 路径
echo ""
echo "2️⃣ 检查 Python 路径..."
if [ -f "venv/bin/python" ]; then
    PYTHON_CMD="./venv/bin/python"
    echo "   ✅ 使用: $PYTHON_CMD"
elif [ -f "venv/Scripts/python.exe" ]; then
    PYTHON_CMD="./venv/Scripts/python.exe"
    echo "   ✅ 使用: $PYTHON_CMD"
else
    echo "   ❌ 找不到 Python 可执行文件！"
    exit 1
fi

# 3. 检查关键依赖
echo ""
echo "3️⃣ 检查关键依赖..."
$PYTHON_CMD -c "import streamlit" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "   ❌ streamlit 未安装"
    echo "   请运行: $PYTHON_CMD -m pip install streamlit"
    exit 1
else
    echo "   ✅ streamlit 已安装"
fi

$PYTHON_CMD -c "
import sys
sys.path.insert(0, 'legacy')
sys.path.insert(0, '.')
from ui.utils import load_css" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "   ⚠️  无法导入 ui.utils，可能有依赖问题"
    echo "   请运行: $PYTHON_CMD -m pip install -r requirements.txt"
else
    echo "   ✅ 核心模块可正常导入"
fi

# 4. 检查端口占用
echo ""
echo "4️⃣ 检查端口 8501..."
if command -v lsof >/dev/null 2>&1; then
    if lsof -Pi :8501 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "   ⚠️  端口 8501 已被占用"
        echo "   正在清理..."
        pkill -f "streamlit run" 2>/dev/null || true
        sleep 2
    else
        echo "   ✅ 端口 8501 可用"
    fi
elif command -v netstat >/dev/null 2>&1; then
    if netstat -an | grep -q ":8501.*LISTEN"; then
        echo "   ⚠️  端口 8501 已被占用"
        echo "   正在清理..."
        pkill -f "streamlit run" 2>/dev/null || true
        sleep 2
    else
        echo "   ✅ 端口 8501 可用"
    fi
else
    echo "   ⚠️  无法检查端口（缺少 lsof/netstat）"
fi

# 5. 检查 legacy/main.py（老系统 Streamlit）
echo ""
echo "5️⃣ 检查 legacy/main.py..."
if [ ! -f "legacy/main.py" ]; then
    echo "   ❌ legacy/main.py 不存在！"
    exit 1
else
    echo "   ✅ legacy/main.py 存在"
fi

# 6. 尝试导入 Streamlit 应用模块（不执行页面）
echo ""
echo "6️⃣ 测试 legacy 路径与 ui 导入..."
$PYTHON_CMD -c "
import sys
sys.path.insert(0, 'legacy')
sys.path.insert(0, '.')
try:
    from ui.utils import load_css
    print('   ✅ legacy/ui 可导入')
except Exception as e:
    print(f'   ❌ 导入失败: {e}')
    sys.exit(1)
" 2>&1

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ 诊断完成：发现导入错误"
    echo "   请查看上面的错误信息"
    exit 1
fi

echo ""
echo "✅ 诊断完成：未发现明显问题"
echo ""
echo "💡 老系统启动："
echo "   $PYTHON_CMD -m streamlit run legacy/main.py --server.port 8501"
echo "💡 新系统（Qiazhi API）："
echo "   $PYTHON_CMD qiazhi/main.py"

