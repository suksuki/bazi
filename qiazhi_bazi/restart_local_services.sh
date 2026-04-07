#!/usr/bin/env bash
set -euo pipefail

# Qiazhi-Bazi local dev services restart (backend 8001, frontend 3001 by default)
# Usage:
#   ./restart_local_services.sh
#   BACKEND_PORT=8001 FRONTEND_PORT=3001 ./restart_local_services.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$SCRIPT_DIR"

BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
LOG_DIR="$ROOT_DIR/.runlogs"
BACKEND_ENV="$BACKEND_DIR/.env"

BACKEND_PORT="${BACKEND_PORT:-8001}"
FRONTEND_PORT="${FRONTEND_PORT:-3001}"

mkdir -p "$LOG_DIR"

echo "[1/4] Stop old processes (ports $FRONTEND_PORT/$BACKEND_PORT)..."
if command -v lsof >/dev/null 2>&1; then
  if lsof -tiTCP:"$FRONTEND_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    lsof -tiTCP:"$FRONTEND_PORT" -sTCP:LISTEN | xargs kill || true
    sleep 1
    if lsof -tiTCP:"$FRONTEND_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
      lsof -tiTCP:"$FRONTEND_PORT" -sTCP:LISTEN | xargs kill -9 || true
    fi
  fi
  if lsof -tiTCP:"$BACKEND_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    lsof -tiTCP:"$BACKEND_PORT" -sTCP:LISTEN | xargs kill || true
    sleep 1
    if lsof -tiTCP:"$BACKEND_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
      lsof -tiTCP:"$BACKEND_PORT" -sTCP:LISTEN | xargs kill -9 || true
    fi
  fi
else
  echo "Warning: lsof not found; skipping port-kill step."
fi

# 额外兜底：清理可能残留的 next dev 进程（避免 chunk 索引错位导致 404 壳页）
if command -v pgrep >/dev/null 2>&1; then
  pgrep -f "next dev -- -p $FRONTEND_PORT" | xargs -r kill || true
  sleep 1
  pgrep -f "next-server" | xargs -r kill || true
fi

echo "[2/4] Start backend ($BACKEND_PORT)..."
if [ -f "$BACKEND_ENV" ]; then
  set -a && source "$BACKEND_ENV" && set +a
fi

nohup bash -lc "cd '$BACKEND_DIR' && set -a && source '$BACKEND_ENV' 2>/dev/null && set +a && PYTHONPATH=. python3 -m uvicorn main:app --host 0.0.0.0 --port '$BACKEND_PORT'" \
  > "$LOG_DIR/backend-$BACKEND_PORT.log" 2>&1 &
BACKEND_PID=$!

sleep 1

echo "[3/4] Start frontend ($FRONTEND_PORT)..."
nohup bash -lc "cd '$FRONTEND_DIR' && npm run dev -- -p '$FRONTEND_PORT'" \
  > "$LOG_DIR/frontend-$FRONTEND_PORT.log" 2>&1 &
FRONTEND_PID=$!

sleep 2

echo "[4/4] Health checks..."
BACKEND_HEALTH="FAIL"
FRONTEND_HEALTH="FAIL"
BACKEND_HTTP_CODE=""
FRONTEND_HTTP_CODE=""
for _ in $(seq 1 20); do
  BACKEND_HTTP_CODE="$(curl -sS -m 3 -o /dev/null -w "%{http_code}" "http://127.0.0.1:$BACKEND_PORT/health" || true)"
  FRONTEND_HTTP_CODE="$(curl -sS -m 3 -o /dev/null -w "%{http_code}" "http://127.0.0.1:$FRONTEND_PORT/" || true)"
  if [ "$BACKEND_HTTP_CODE" = "200" ] && [ "$FRONTEND_HTTP_CODE" = "200" ]; then
    BACKEND_HEALTH="OK"
    FRONTEND_HEALTH="OK"
    break
  fi
  sleep 1
done

echo ""
echo "====== Local Dev Services ======"
echo "Backend PID : $BACKEND_PID (health: $BACKEND_HEALTH, http: ${BACKEND_HTTP_CODE:-N/A})"
echo "Frontend PID: $FRONTEND_PID (health: $FRONTEND_HEALTH, http: ${FRONTEND_HTTP_CODE:-N/A})"
echo "Backend URL : http://127.0.0.1:$BACKEND_PORT/health"
echo "Frontend URL: http://127.0.0.1:$FRONTEND_PORT/"
echo "Backend Log : $LOG_DIR/backend-$BACKEND_PORT.log"
echo "Frontend Log: $LOG_DIR/frontend-$FRONTEND_PORT.log"
echo "=================================="

