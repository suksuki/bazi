#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="/Users/liujin/DEV/AIProjects/bazi/qiazhi_bazi"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
LOG_DIR="$ROOT_DIR/.runlogs"
BACKEND_ENV="$BACKEND_DIR/.env"

mkdir -p "$LOG_DIR"

echo "[1/4] 停止旧进程 (3000/8001)..."
if lsof -tiTCP:3000 -sTCP:LISTEN >/dev/null 2>&1; then
  lsof -tiTCP:3000 -sTCP:LISTEN | xargs kill -9
fi
if lsof -tiTCP:8001 -sTCP:LISTEN >/dev/null 2>&1; then
  lsof -tiTCP:8001 -sTCP:LISTEN | xargs kill -9
fi

echo "[2/4] 启动后端 8001..."
if [ -f "$BACKEND_ENV" ]; then
  # shellcheck disable=SC1090
  set -a && source "$BACKEND_ENV" && set +a
fi
if command -v pg_isready >/dev/null 2>&1; then
  if ! pg_isready -h 192.168.0.13 -p 5432 >/dev/null 2>&1; then
    echo "PostgreSQL(192.168.0.13:5432) 未就绪，拒绝启动。"
    exit 1
  fi
else
  echo "未检测到 pg_isready，改用 Python 连接探测 PostgreSQL..."
  if ! python3 - <<'PY'
import os
import sys
from sqlalchemy import create_engine, text

db_url = os.getenv("DATABASE_URL", "")
if not db_url:
    print("DATABASE_URL 未配置。")
    sys.exit(1)
try:
    engine = create_engine(db_url, echo=False, pool_pre_ping=True)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("PostgreSQL 连接探测通过。")
except Exception as e:  # noqa: BLE001
    print(f"PostgreSQL 连接探测失败: {e}")
    sys.exit(1)
PY
  then
    echo "PostgreSQL 不可用，拒绝启动。"
    exit 1
  fi
fi
nohup bash -lc "cd \"$BACKEND_DIR\" && set -a && source \"$BACKEND_ENV\" && set +a && PYTHONPATH=. python3 -m uvicorn main:app --host 0.0.0.0 --port 8001" \
  > "$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!

sleep 1
echo "[3/4] 启动前端 3000..."
nohup bash -lc "cd \"$FRONTEND_DIR\" && npm run dev" \
  > "$LOG_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!

sleep 2
echo "[4/4] 健康检查..."
BACKEND_HEALTH="FAIL"
if curl -sS -m 3 "http://127.0.0.1:8001/health" >/dev/null 2>&1; then
  BACKEND_HEALTH="OK"
fi

FRONTEND_HEALTH="FAIL"
if curl -sS -m 3 "http://127.0.0.1:3000/" >/dev/null 2>&1; then
  FRONTEND_HEALTH="OK"
fi

echo ""
echo "====== Dev Services ======"
echo "Backend PID : $BACKEND_PID (health: $BACKEND_HEALTH)"
echo "Frontend PID: $FRONTEND_PID (health: $FRONTEND_HEALTH)"
echo "Backend URL : http://127.0.0.1:8001/health"
echo "Frontend URL: http://127.0.0.1:3000"
echo "Backend Log : $LOG_DIR/backend.log"
echo "Frontend Log: $LOG_DIR/frontend.log"
echo "=========================="
