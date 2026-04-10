#!/usr/bin/env bash
set -euo pipefail

# Qiazhi-Bazi services restart (backend 8001, frontend 3001 by default)
# Usage:
#   ./restart_local_services.sh
#   FRONTEND_MODE=prod ./restart_local_services.sh
#   FRONTEND_MODE=dev BACKEND_PORT=8001 FRONTEND_PORT=3001 ./restart_local_services.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$SCRIPT_DIR"

BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
LOG_DIR="$ROOT_DIR/.runlogs"
BACKEND_ENV="$BACKEND_DIR/.env"

BACKEND_PORT="${BACKEND_PORT:-8001}"
FRONTEND_PORT="${FRONTEND_PORT:-3001}"
FRONTEND_MODE="${FRONTEND_MODE:-prod}" # dev | prod
# 生产模式下跳过前端 pnpm build（仅重启进程；需已有 frontend/.next）
SKIP_BUILD="${SKIP_BUILD:-0}"

mkdir -p "$LOG_DIR"

echo "[1/5] Stop old processes (ports $FRONTEND_PORT/$BACKEND_PORT)..."
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
  echo "Warning: lsof not found; using fuser/ss fallback."
  if command -v fuser >/dev/null 2>&1; then
    fuser -k "${FRONTEND_PORT}/tcp" || true
    fuser -k "${BACKEND_PORT}/tcp" || true
  elif command -v ss >/dev/null 2>&1; then
    FRONT_PIDS="$(ss -ltnp "sport = :$FRONTEND_PORT" 2>/dev/null | sed -n 's/.*pid=\([0-9]\+\).*/\1/p' | sort -u)"
    BACK_PIDS="$(ss -ltnp "sport = :$BACKEND_PORT" 2>/dev/null | sed -n 's/.*pid=\([0-9]\+\).*/\1/p' | sort -u)"
    if [ -n "$FRONT_PIDS" ]; then
      echo "$FRONT_PIDS" | xargs -r kill || true
    fi
    if [ -n "$BACK_PIDS" ]; then
      echo "$BACK_PIDS" | xargs -r kill || true
    fi
  fi
fi

echo "[2/5] Start backend ($BACKEND_PORT)..."
if [ -f "$BACKEND_ENV" ]; then
  set -a && source "$BACKEND_ENV" && set +a
fi

nohup bash -lc "cd '$BACKEND_DIR' && set -a && source '$BACKEND_ENV' 2>/dev/null && set +a && PYTHONPATH=. python3 -m uvicorn main:app --host 0.0.0.0 --port '$BACKEND_PORT'" \
  > "$LOG_DIR/backend-$BACKEND_PORT.log" 2>&1 &
BACKEND_PID=$!

sleep 1

echo "[3/5] Prepare frontend runtime ($FRONTEND_MODE)..."
FRONTEND_LOG="$LOG_DIR/frontend-$FRONTEND_PORT.log"
if [ "$FRONTEND_MODE" = "prod" ]; then
  if [ "$SKIP_BUILD" = "1" ]; then
    echo "SKIP_BUILD=1 → 跳过 pnpm build（使用现有 .next）"
  elif command -v pnpm >/dev/null 2>&1; then
    (cd "$FRONTEND_DIR" && pnpm build)
  else
    (cd "$FRONTEND_DIR" && npm run build)
  fi
fi

echo "[4/5] Start frontend ($FRONTEND_PORT, mode=$FRONTEND_MODE)..."
if [ "$FRONTEND_MODE" = "dev" ]; then
  if command -v pnpm >/dev/null 2>&1; then
    nohup bash -lc "cd '$FRONTEND_DIR' && pnpm dev -- -p '$FRONTEND_PORT'" > "$FRONTEND_LOG" 2>&1 &
  else
    nohup bash -lc "cd '$FRONTEND_DIR' && npm run dev -- -p '$FRONTEND_PORT'" > "$FRONTEND_LOG" 2>&1 &
  fi
else
  if command -v pnpm >/dev/null 2>&1; then
    nohup bash -lc "cd '$FRONTEND_DIR' && pnpm start -p '$FRONTEND_PORT'" > "$FRONTEND_LOG" 2>&1 &
  else
    nohup bash -lc "cd '$FRONTEND_DIR' && npm run start -- -p '$FRONTEND_PORT'" > "$FRONTEND_LOG" 2>&1 &
  fi
fi
FRONTEND_PID=$!

sleep 2

echo "[5/5] Health checks..."
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
echo "FrontendMode: $FRONTEND_MODE"
echo "Backend Log : $LOG_DIR/backend-$BACKEND_PORT.log"
echo "Frontend Log: $FRONTEND_LOG"
echo "=================================="

