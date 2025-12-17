#!/bin/bash
# 快捷启动脚本 - 指向 scripts/evolution/start_evolution.sh
exec bash "$(dirname "$0")/scripts/evolution/start_evolution.sh" "$@"

