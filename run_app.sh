#!/bin/bash
# 运行 APP 的脚本（Shell 版本）

echo "🚀 启动八字预测系统 (Bazi Prediction System)"
echo "=============================================="
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "⚠️  警告: 未找到虚拟环境 (venv/)"
    echo "   请先创建虚拟环境: python3 -m venv venv"
    echo ""
    USE_VENV=false
else
    echo "✅ 找到虚拟环境"
    USE_VENV=true
fi

# 检查 main.py
if [ ! -f "main.py" ]; then
    echo "❌ 错误: 未找到 main.py"
    exit 1
fi

echo "✅ 找到主程序: main.py"
echo ""

# 设置环境变量
export PYTHONUNBUFFERED=1
export STREAMLIT_SERVER_FILE_WATCHER_TYPE=poll
export STREAMLIT_SERVER_RUN_ON_SAVE=true
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# 获取 WSL IP（如果在 WSL 中）
WSL_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "localhost")

echo "🌐 访问地址:"
echo "   - 本地: http://localhost:8501"
if [ "$WSL_IP" != "localhost" ]; then
    echo "   - 网络: http://$WSL_IP:8501"
fi
echo ""
echo "💡 提示: 按 Ctrl+C 停止服务器"
echo "=============================================="
echo ""

# 构建启动命令
if [ "$USE_VENV" = true ]; then
    STREAMLIT_CMD="./venv/bin/streamlit"
else
    STREAMLIT_CMD="streamlit"
fi

# 启动 Streamlit
$STREAMLIT_CMD run main.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.fileWatcherType poll

