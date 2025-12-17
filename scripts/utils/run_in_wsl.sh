#!/bin/bash
# WSL 执行包装脚本 - 消除路径转换警告
# 使用方法: wsl -e bash scripts/run_in_wsl.sh <command>

# 切换到正确的目录（使用 Linux 路径）
cd /home/jin/bazi_predict

# 激活虚拟环境
source venv/bin/activate

# 执行传入的命令
exec "$@"

