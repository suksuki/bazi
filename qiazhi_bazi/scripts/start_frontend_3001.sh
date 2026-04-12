#!/usr/bin/env bash
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPTS="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=/dev/null
source "$SCRIPTS/_free_port.sh"
LOG_DIR="$REPO/.runlogs"
mkdir -p "$LOG_DIR"
cd "$REPO/frontend"
_free_tcp_port 3001 || true
pkill -f "next start.*3001" 2>/dev/null || true
pkill -f "next-server.*3001" 2>/dev/null || true
sleep 1
nohup pnpm exec next start -p 3001 >>"$LOG_DIR/frontend-3001.log" 2>&1 &
NX_PID=$!
echo "next pid $NX_PID  log $LOG_DIR/frontend-3001.log"

_port_up() {
  if command -v ss >/dev/null 2>&1; then
    ss -ltn "sport = :3001" 2>/dev/null | grep -q LISTEN
  else
    curl -sf -m 1 "http://127.0.0.1:3001/" >/dev/null 2>&1
  fi
}
for _ in $(seq 1 60); do
  if _port_up; then break; fi
  if ! kill -0 "$NX_PID" 2>/dev/null; then
    echo "ERROR: next 已退出，见日志尾部：" >&2
    tail -30 "$LOG_DIR/frontend-3001.log" >&2
    exit 1
  fi
  sleep 0.25
done
if ! _port_up; then
  echo "ERROR: 3001 未监听（超时）" >&2
  tail -30 "$LOG_DIR/frontend-3001.log" >&2
  exit 1
fi
echo "3001 已就绪"
