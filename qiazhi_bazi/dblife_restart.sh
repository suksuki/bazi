#!/usr/bin/env bash
set -euo pipefail

# dblife / Qiazhi 生产机：停旧进程 →（可选）清 .next → 前端 build → 拉起后端 + 前端
# 在仓库根目录执行:  ~/bazi/qiazhi_bazi/dblife_restart.sh
#
# 用法:
#   ./dblife_restart.sh              # 默认：不清 .next，全量 build + 重启（与 restart_local_services.sh 相同）
#   ./dblife_restart.sh --clean      # 先 rm -rf frontend/.next 再 build（大版本/怀疑构建脏时）
#   ./dblife_restart.sh --no-build   # 只杀端口并重启进程，不跑 pnpm build（仅改环境变量等）
#
# 说明:
# - 「浏览器清缓存」在客户端做，本脚本只管服务器进程与前端构建。
# - 端口默认: 后端 8001，前端 3001（可用环境变量覆盖）。

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

CLEAN_NEXT=0
NO_BUILD=0
for arg in "$@"; do
  case "$arg" in
    --clean) CLEAN_NEXT=1 ;;
    --no-build) NO_BUILD=1 ;;
    -h|--help)
      grep -E '^# |^#' "$0" | sed 's/^# //;s/^#//'
      exit 0
      ;;
  esac
done

if [ "$CLEAN_NEXT" = "1" ] && [ "$NO_BUILD" = "1" ]; then
  echo "错误: --clean 与 --no-build 不能同时使用（清空 .next 后必须执行 build）" >&2
  exit 1
fi

if [ "$CLEAN_NEXT" = "1" ]; then
  echo "[dblife_restart] 清理 frontend/.next ..."
  rm -rf "$ROOT/frontend/.next"
fi

if [ "$NO_BUILD" = "1" ]; then
  echo "[dblife_restart] 跳过前端构建，仅重启服务..."
  export SKIP_BUILD=1
else
  export SKIP_BUILD=0
fi

exec "$ROOT/restart_local_services.sh"
