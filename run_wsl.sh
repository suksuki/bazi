#!/bin/bash

# 获取脚本所在目录的绝对路径
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$PROJECT_DIR"

echo "🚀 Starting AI Bazi PRO in WSL..."
echo "📂 Project Directory: $PROJECT_DIR"

# 检查虚拟环境
if [ -d "venv" ]; then
    echo "🐍 Activating virtual environment..."
    source venv/bin/activate
else
    echo "⚠️ Warning: venv folder not found. Attempting to run without activation."
fi

# 启动 Streamlit
echo "✨ Launching Streamlit application..."
streamlit run main.py
