#!/bin/bash

# AI Bazi 稳定启动脚本
# 优化配置，减少不必要的重载

echo "🚀 启动 AI Bazi 预测系统（优化模式）"
echo "================================"

# 1. 清理旧进程
echo "📌 清理旧的 Streamlit 进程..."
pkill -f "streamlit run" || true
sleep 1

# 2. 检查并安装依赖
echo "📦 检查依赖..."
./venv/bin/pip install -q -r requirements.txt

# 3. 设置环境变量以优化性能
export PYTHONUNBUFFERED=1
export STREAMLIT_SERVER_FILE_WATCHER_TYPE=poll
export STREAMLIT_SERVER_RUN_ON_SAVE=true
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# 4. 创建必要的目录（避免运行时创建触发reload）
mkdir -p data/books data/logs data/profiles .streamlit

# 5. 显示配置信息
echo ""
echo "⚙️  当前配置："
echo "   - 文件监控模式: poll (稳定模式)"
echo "   - 热重载: 启用（仅代码文件）"
echo "   - 忽略目录: data/, logs/, venv/"
echo ""

# 6. 启动服务器
echo "🔮 启动服务器..."
echo "   访问地址: http://localhost:8501"
echo "   网络地址: http://$(hostname -I | awk '{print $1}'):8501"
echo ""
echo "💡 提示: 如果仍然频繁重载，可以："
echo "   1. 在 .streamlit/config.toml 中设置 runOnSave = false"
echo "   2. 增加 scheduler.py 中的 check_interval 值"
echo "   3. 使用生产模式: streamlit run main.py --server.headless=true"
echo ""

# 启动（带日志重定向）
./venv/bin/streamlit run main.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.fileWatcherType poll \
    2>&1 | tee server.log
