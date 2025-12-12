#!/bin/bash

# 系统WSL直接启动脚本 - 简洁稳定版
# 解决视频处理导致的频繁重载问题

echo "🚀 AI Bazi - WSL 稳定启动（无IDE干扰）"
echo "=========================================="

# 1. 清理旧进程
pkill -9 -f "streamlit run" 2>/dev/null || true
sleep 1

# 2. 关键环境变量（针对视频处理优化）
export PYTHONUNBUFFERED=1
export STREAMLIT_SERVER_FILE_WATCHER_TYPE=poll  # poll模式够用
export STREAMLIT_SERVER_RUN_ON_SAVE=true        # 可以保留热重载

# 3. 预创建目录（避免运行时创建）
mkdir -p data/{books,logs,profiles} .streamlit 2>/dev/null

# 4. 获取WSL IP
WSL_IP=$(hostname -I | awk '{print $1}')

echo ""
echo "✅ 配置完成："
echo "   - 文件监控: poll (稳定模式)"
echo "   - 热重载: 启用 (仅 .py 文件)"
echo "   - 数据文件变化: 不会触发重载"
echo ""
echo "🌐 访问地址："
echo "   WSL终端: http://localhost:8501"
echo "   Windows浏览器: http://$WSL_IP:8501"
echo ""
echo "💡 提示: Ctrl+C 停止服务器"
echo "=========================================="
echo ""

# 5. 启动（输出到屏幕，方便观察）
./venv/bin/streamlit run main.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.fileWatcherType poll
