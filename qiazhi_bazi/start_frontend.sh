#!/usr/bin/env bash
set -euo pipefail

# 仅启动 Qiazhi 前端（Next.js），默认生产模式 + 端口 3001，供 Nginx 反代。
# 放在: ~/bazi/qiazhi_bazi/start_frontend.sh
#
# 用法:
#   ./start_frontend.sh                    # 停旧进程 → pnpm build → 后台 next start
#   SKIP_BUILD=1 ./start_frontend.sh       # 仅重启（进程挂了、未改前端代码时）
#   FRONTEND_MODE=dev ./start_frontend.sh  # 开发模式 next dev（勿对公网反代）
#   FOREGROUND=1 ./start_frontend.sh       # 前台运行，便于看日志
#   FRONTEND_PORT=3002 ./start_frontend.sh # 换端口
#
# 环境变量: FRONTEND_PORT FRONTEND_MODE SKIP_BUILD FOREGROUND

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
LOG_DIR="$SCRIPT_DIR/.runlogs"
FRONTEND_PORT="${FRONTEND_PORT:-3001}"
FRONTEND_MODE="${FRONTEND_MODE:-prod}" # prod | dev
SKIP_BUILD="${SKIP_BUILD:-0}"
FOREGROUND="${FOREGROUND:-0}"

for arg in "$@"; do
  case "$arg" in
    --no-build) SKIP_BUILD=1 ;;
    --dev) FRONTEND_MODE=dev ;;
    --foreground) FOREGROUND=1 ;;
    -h|--help)
      grep -E '^# |^#  ' "$0" | sed 's/^# //;s/^#//'
      exit 0
      ;;
  esac
done

mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/frontend-${FRONTEND_PORT}.log"

kill_port() {
  local port="$1"
  if command -v lsof >/dev/null 2>&1; then
    if lsof -tiTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
      lsof -tiTCP:"$port" -sTCP:LISTEN | xargs kill || true
      sleep 1
      if lsof -tiTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
        lsof -tiTCP:"$port" -sTCP:LISTEN | xargs kill -9 || true
      fi
    fi
    return 0
  fi
  if command -v fuser >/dev/null 2>&1; then
    fuser -k "${port}/tcp" 2>/dev/null || true
    return 0
  fi
  if command -v ss >/dev/null 2>&1; then
    local pids
    pids="$(ss -ltnp "sport = :$port" 2>/dev/null | sed -n 's/.*pid=\([0-9]\+\).*/\1/p' | sort -u)"
    if [ -n "$pids" ]; then
      echo "$pids" | xargs -r kill || true
      sleep 1
      echo "$pids" | xargs -r kill -9 2>/dev/null || true
    fi
  fi
}

echo "[1/3] 释放端口 $FRONTEND_PORT ..."
kill_port "$FRONTEND_PORT"

cd "$FRONTEND_DIR"

if [ "$FRONTEND_MODE" = "dev" ]; then
  echo "[2/3] 开发模式: next dev -p $FRONTEND_PORT"
  if [ "$FOREGROUND" = "1" ]; then
    exec pnpm dev -- -p "$FRONTEND_PORT"
  fi
  nohup pnpm dev -- -p "$FRONTEND_PORT" >"$LOG_FILE" 2>&1 &
  echo "[3/3] 已后台启动 PID=$! 日志: $LOG_FILE"
  exit 0
fi

if [ "$SKIP_BUILD" != "1" ]; then
  echo "[2/3] 生产构建: pnpm build"
  pnpm build
else
  echo "[2/3] 跳过构建 (SKIP_BUILD=1)"
fi

echo "[3/3] 生产启动: next start -p $FRONTEND_PORT"
if [ "$FOREGROUND" = "1" ]; then
  exec pnpm start -p "$FRONTEND_PORT"
fi

nohup pnpm start -p "$FRONTEND_PORT" >"$LOG_FILE" 2>&1 &
echo "已后台启动 PID=$! 日志: $LOG_FILE"
sleep 1
if command -v curl >/dev/null 2>&1; then
  code="$(curl -sS -o /dev/null -w "%{http_code}" "http://127.0.0.1:${FRONTEND_PORT}/" || true)"
  echo "本机探测: http://127.0.0.1:${FRONTEND_PORT}/ → HTTP $code"
fi
