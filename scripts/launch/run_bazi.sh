#!/bin/bash
# 基础启动脚本 - 快速启动 Bazi 系统

# Kill previous instances
pkill -f streamlit || true

# 安装依赖
./venv/bin/pip install -r requirements.txt

# 启动 Streamlit
./venv/bin/streamlit run main.py --server.port 8501 --server.address 0.0.0.0
