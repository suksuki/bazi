#!/bin/bash

# WSL2 专用启动脚本 - 最大化稳定性
# 针对视频处理和WSL文件系统特性优化

echo "🐧 WSL2 环境 - AI Bazi 稳定启动"
echo "==========================================="

# 检测WSL环境
if ! grep -qi microsoft /proc/version; then
    echo "⚠️  警告: 似乎不在WSL环境中运行"
    echo "此脚本针对WSL2优化，在其他环境可能不是最优"
    read -p "继续? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 1. 清理旧进程
echo "📌 清理旧的 Streamlit 进程..."
pkill -9 -f "streamlit run" 2>/dev/null || true
sleep 1

# 2. WSL 特定环境变量
echo "⚙️  设置 WSL 优化环境变量..."
export PYTHONUNBUFFERED=1
export STREAMLIT_SERVER_FILE_WATCHER_TYPE=none  # WSL下建议完全禁用
export STREAMLIT_SERVER_RUN_ON_SAVE=false        # 禁用热重载
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# WSL2 inotify 优化
export WATCHMAN_ENABLE_INOTIFY=0

# 3. 检查并创建外部数据目录（可选但推荐）
EXTERNAL_DATA="$HOME/bazi_data_external"
if [ ! -d "$EXTERNAL_DATA" ]; then
    echo "📁 首次运行：创建外部数据目录..."
    mkdir -p "$EXTERNAL_DATA"/{books,logs,profiles}
    
    # 如果有现有data目录，询问是否迁移
    if [ -d "data" ] && [ ! -L "data" ]; then
        echo ""
        echo "检测到现有 data/ 目录"
        read -p "是否迁移到外部目录以提升稳定性? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "迁移数据..."
            cp -r data/* "$EXTERNAL_DATA/"
            mv data data.backup
            ln -s "$EXTERNAL_DATA" data
            echo "✅ 数据已迁移并创建符号链接"
        fi
    fi
fi

# 4. 检查依赖
echo "📦 检查 Python 依赖..."
./venv/bin/pip install -q -r requirements.txt

# 5. 预创建必要目录
mkdir -p data/books data/logs data/profiles .streamlit 2>/dev/null || true

# 6. 清理临时文件（减少文件监控负担）
echo "🧹 清理临时文件..."
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# 7. WSL性能提示
echo ""
echo "💡 WSL2 优化建议："
echo "   1. 项目应在 WSL 文件系统 (~/...) 而非 /mnt/c/..."
echo "   2. 已禁用热重载 - 代码修改需手动重启"
echo "   3. 视频处理数据不会触发重载"
echo ""

# 8. 显示当前位置
CURRENT_PATH=$(pwd)
if [[ $CURRENT_PATH == /mnt/* ]]; then
    echo "⚠️  警告: 项目在 Windows 文件系统 ($CURRENT_PATH)"
    echo "   建议迁移到 WSL 文件系统以获得最佳性能:"
    echo "   cp -r $CURRENT_PATH ~/bazi_predict"
    echo ""
else
    echo "✅ 项目在 WSL 文件系统: $CURRENT_PATH"
fi

# 9. 检查端口占用
if lsof -Pi :8501 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  端口 8501 已被占用，尝试清理..."
    kill $(lsof -t -i:8501) 2>/dev/null || true
    sleep 1
fi

# 10. 获取WSL IP（方便从Windows访问）
WSL_IP=$(hostname -I | awk '{print $1}')

echo ""
echo "🚀 启动服务器（生产模式 - 无热重载）"
echo "==========================================="
echo "   WSL 内访问: http://localhost:8501"
echo "   Windows 访问: http://$WSL_IP:8501"
echo ""
echo "   按 Ctrl+C 停止服务器"
echo "   代码修改后需重启此脚本"
echo "==========================================="
echo ""

# 11. 启动服务器（无文件监控模式）
./venv/bin/streamlit run main.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --server.fileWatcherType none \
    --server.runOnSave false \
    2>&1 | tee server.log
