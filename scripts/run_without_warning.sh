#!/bin/bash
# 运行脚本时过滤 WSL 路径警告
# 使用方法: bash scripts/run_without_warning.sh <script> [args...]

cd /home/jin/bazi_predict
source venv/bin/activate

# 运行命令并过滤 WSL 警告
# 使用 sed 过滤掉包含 "Failed to translate" 的行
exec "$@" 2>&1 | sed '/Failed to translate/d'

