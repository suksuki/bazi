#!/bin/bash

# Bazi System Stability Launcher (Process Separation Mode)
# Created by Antigravity to solve "Reload Window" OOM crashes.

# Ensure directories exist
mkdir -p data/logs data/books data/media_cache

# 0. Cleanup previous ghosts
echo "🧹 Cleaning up previous processes..."
pkill -f "streamlit run main.py"
pkill -f "python run_worker.py"
sleep 1

# 1. Environment Setup
export STREAMLIT_SERVER_FILE_WATCHER_TYPE=poll
export STREAMLIT_SERVER_RUN_ON_SAVE=true
export DISABLE_EMBEDDED_WORKER=true
export OLLAMA_HOST=http://localhost:11434

echo "🚀 Starting Bazi System in STABLE SPLIT MODE..."
echo "---------------------------------------------"

# 2. Start Background Worker (Independent Process)
echo "▶️  Starting AI Background Worker..."
nohup ./venv/bin/python run_worker.py > data/logs/worker_service.log 2>&1 &
WORKER_PID=$!
echo "   ✅ Worker running on PID: $WORKER_PID (Logs: data/logs/worker_service.log)"

# 3. Start UI Server (Main Process)
echo "▶️  Starting Streamlit UI..."
./venv/bin/streamlit run main.py --server.port 8501 --server.address 0.0.0.0

# 4. Cleanup on Exit
echo "🛑 Shutting down..."
kill $WORKER_PID
echo "👋 Bye!"
