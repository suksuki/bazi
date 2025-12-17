#!/bin/bash
# 快捷启动脚本 - 指向 scripts/launch/run_bazi.sh
exec bash "$(dirname "$0")/scripts/launch/run_bazi.sh" "$@"

