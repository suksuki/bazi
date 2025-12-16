#!/bin/bash
# 训练脚本包装器
# 注意: WSL 路径转换警告 (Failed to translate Z:\...) 是 WSL 内部警告，不影响功能
# 这个警告是因为 Cursor 传递 Windows 工作目录导致的，无法完全消除

cd /home/jin/bazi_predict
source venv/bin/activate

# 执行训练脚本
exec python3 scripts/train_model_optuna.py "$@"

