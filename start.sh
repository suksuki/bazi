#!/bin/bash
# 快捷启动脚本 - 指向 scripts/launch/start.sh
exec bash "$(dirname "$0")/scripts/launch/start.sh" "$@"

