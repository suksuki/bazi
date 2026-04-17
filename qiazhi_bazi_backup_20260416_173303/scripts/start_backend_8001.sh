#!/usr/bin/env bash
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPTS="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=/dev/null
source "$SCRIPTS/_free_port.sh"
LOG_DIR="$REPO/.runlogs"
mkdir -p "$LOG_DIR"
cd "$REPO/backend"
if [ -f .env ]; then set -a && source ./.env && set +a; fi
_free_tcp_port 8001 || true
pkill -f "uvicorn main:app --host 127.0.0.1 --port 8001" 2>/dev/null || true
sleep 1
nohup env PYTHONPATH=. python3 -m uvicorn main:app --host 127.0.0.1 --port 8001 \
  >>"$LOG_DIR/backend-8001.log" 2>&1 &
UV_PID=$!
echo "uvicorn pid $UV_PID  log $LOG_DIR/backend-8001.log"

_port_up() {
  if command -v ss >/dev/null 2>&1; then
    ss -ltn "sport = :8001" 2>/dev/null | grep -q LISTEN
  else
    curl -sf -m 1 "http://127.0.0.1:8001/health" >/dev/null 2>&1
  fi
}
for _ in $(seq 1 40); do
  if _port_up; then break; fi
  if ! kill -0 "$UV_PID" 2>/dev/null; then
    echo "ERROR: uvicorn 已退出，见日志尾部：" >&2
    tail -25 "$LOG_DIR/backend-8001.log" >&2
    exit 1
  fi
  sleep 0.25
done
if ! _port_up; then
  echo "ERROR: 8001 未监听（超时）" >&2
  tail -25 "$LOG_DIR/backend-8001.log" >&2
  exit 1
fi
echo "8001 已就绪"
